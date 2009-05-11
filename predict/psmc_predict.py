"""
========================
psmc_predict
========================

Overview
-----------
This code uses the two-mass thermal model to predict PSMC temperatures 1PIN1AT
and 1PDEAAT.  It can evaluate the model for times in the past (model validation
and trending) or in the future (PSMC backstop checker).  The mode depends on
whether an ``oflsdir`` is supplied.

Command line options
---------------------
 =================== ========================================  ===================
 Option              Description                                Default
 =================== ========================================  ===================
 help                Show help message and exit
 outdir=OUTDIR       Output directory                          None (interactive)
 oflsdir=OFLSDIR     Load products OFLS directory              None
 power=POWER         Starting PSMC power (watts)               From telemetry
 simpos=SIMPOS       Starting SIM-Z position (steps)           From telemetry
 pitch=PITCH         Starting pitch (deg)                      From telemetry
 T_dea=T_DEA         Starting 1pdeaat temperature (degC)       From telemetry
 T_pin=T_PIN         Starting 1pin1at temperature (degC)       From telemetry
 tstart=TSTART       Start time (any valid datetime format)    None
 tstop=TSTOP         Stop time (any valid datetime format)     None
 dt=DT               Time step for model evaluation (sec)      32.8
 verbose=VERBOSE     Verbosity (0=quiet, 1=normal, 2=debug)    1 (normal)
 =================== ========================================  ===================

If the ``--outdir`` option is specified then the output plots are created as
PNG files and the report information goes into output text files in that
directory.  The latter are processed to generate an HTML report.

With no ``--outdir`` option the report information is printed to the screen and
the plots are opened as plot windows that can be manipulated interactively.

The model starting parameters (temperature and spacecraft state) can be
specified in one of two ways:

 - Provide all of the ``power``, ``simpos``, ``pitch``, ``T_dea``, and ``T_pin``
   command line options corresponding to the expected state at the
   load start time.  This may be necessary in the event of complex replan
   situations where the second option fails to capture the correct starting
   state.  In this case the ``cmd_states`` table is not used.

 - Provide none of the above command line options.  In this case the tool
   will propagate forward from a 5-minute average of the last available
   telemetry using the ``cmd_states`` table.  This table contains expected
   commanding from the approved command loads in the operations database.  This
   is the default usage.

Backstop checker
-----------------

If the ``--oflsdir=OFLSDIR`` option is supplied then the tool runs in backstop
mode and predicts PSMC temperatures based on the specified commanding in the
backstop file ``*.backstop`` in the ``OFLSDIR``.

In backstop mode the ``tstart`` and ``tstop`` values are taken from the backstop
file and supplied command line values are ignored.

Model validation and trending
-----------------------------

If the ``oflsdir`` parameter is not supplied then the PSMC model is propagated
between the (required) ``tstart`` and ``tstop`` parameters.  The starting
temperatures and state are taken either from command-line options or from
5-minute averages at ``tstart``.

The thermal model is propagated using the ``cmd_states`` database table which
must be available over the specified time interval.
"""

import sys
import os
import glob
import logging
from pprint import pformat
import datetime
import re
import time
import shutil

import numpy as np
import Ska.ParseCM
import Ska.DBI
import twodof
import Ska.Table
import Ska.TelemArchive.fetch
from Chandra.Time import DateTime
from quaternion import Quat
import characteristics
import state_commands
import states

# Matplotlib setup
# Use Agg backend for command-line (non-interactive) operation
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import Ska.Matplotlib

# Django setup (used for template rendering)
import django.template
import django.conf
try:
    django.conf.settings.configure()
except RuntimeError, msg:
    print msg

MSID = dict(dea='1PDEAAT', pin='1PIN1AT')
YELLOW = dict(dea=characteristics.T_dea_yellow, pin=characteristics.T_pin_yellow)
MARGIN = dict(dea=characteristics.T_dea_margin, pin=characteristics.T_pin_margin)

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--outdir",
                      default="psmc_check",
                      help="Output directory")
    parser.add_option("--oflsdir",
                      default="/data/mpcrit1/mplogs/2008/JUN2308/oflsa",
                      help="Load products OFLS directory")
    parser.add_option("--power",
                      type='float',
                      help="Starting PSMC power (watts)")
    parser.add_option("--simpos",
                      type='float',
                      help="Starting SIM-Z position (steps)")
    parser.add_option("--pitch",
                      type='float',
                      help="Starting pitch (deg)")
    parser.add_option("--T_dea",
                      type='float',
                      help="Starting 1pdeaat temperature (degC)")
    parser.add_option("--T_pin",
                      type='float',
                      help="Starting 1pin1at temperature (degC)")
    parser.add_option("--tstart",
                      help="Start time (any valid datetime format)")
    parser.add_option("--tstop",
                      help="Stop time (any valid datetime format)")
    parser.add_option("--dt",
                      type='float',
                      default=32.8,
                      help="Time step for model evaluation (sec)")
    parser.add_option("--traceback",
                      default=True,
                      help='Enable tracebacks')
    parser.add_option("--verbose",
                      type='int',
                      default=2,
                      help="Verbosity (0=quiet, 1=normal, 2=debug)")

    opt, args = parser.parse_args()
    return opt, args

def main(opt):
    if not os.path.exists(opt.outdir):
        os.mkdir(opt.outdir)
    config_logging(opt)
    logging.debug('Options: %s' % pformat(opt.__dict__))

    # Connect to database
    logging.debug('Connecting to database to get cmd_states')
    db = Ska.DBI.DBI(dbi='sybase', server='sybase', user='aca_ops', database='aca')

    # Set tstart, tstop and bs_cmds depending on opt.oflsdir
    tstart, tstop, bs_cmds = get_times_bs_cmds(opt)
        
    # Store info relevant to processing for use in outputs
    proc = dict(datestart=DateTime(tstart).date,
                datestop=DateTime(tstop).date,
                run_user=os.environ['USER'],
                run_time=time.ctime(),
                errors=[],
                dea_limit=YELLOW['dea'] - MARGIN['dea'],
                pin_limit=YELLOW['pin'] - MARGIN['pin'],
                )
    # Make initial pseudo-state from cmd line options
    state0 = dict((x, getattr(opt, x)) for x in ('pitch', 'simpos', 'power', 'T_dea', 'T_pin'))
    state0.update({'tstart': tstart-30, 'tstop': tstart})

    # If cmd lines options were not fully specified then make state0 from
    # telemetry (for temps) and cmd_states table (for rest).  State0 will
    # end at the time of the last available telemetry before tstart.
    if None in state0.values():
        state0 = get_state0_cmd_tlm(db, tstart)

    logging.debug('state0 at %s is\n%s' % (DateTime(state0['tstart']).date,
                                           pformat(state0)))

    # Get the commands after end of state0 through first backstop command time
    # or tstop (if no backstop commands)
    db_cmds = get_cmds(db, datestart=DateTime(state0['tstop']).date,
                       datestop=(DateTime(bs_cmds[0]['time']).date if bs_cmds else proc['datestop']))

    cmds = state_commands.reduced_backstop(db_cmds + bs_cmds,
                                           init_quat=Quat(*[state0[x] for x in ('q1','q2','q3','q4')]))
    states = states.get_states(state0, cmds)
    logging.info('Commanded states from %s to %s\n' % (states[0]['datestart'],
                                                       states[-1]['datestop']))

    # Add power column based on ACIS commanding in states
    states = Ska.Numpy.add_column(states, 'power', get_power(states))

    times = np.arange(state0['tstop'], tstop, opt.dt)
    T_pin, T_dea = twodof.calc_twodof_model(states, state0['T_pin'], state0['T_dea'], times)
    
    temps = dict(dea=T_dea, pin=T_pin)
    plots = make_plots(opt, states, times, temps)
    viols = make_viols(opt, states, times, temps)
    write_states(opt, states)
    write_temps(opt, times, temps)
    write_index_rst(opt, plots, viols, proc)
    rst_to_html(opt, proc)

    return dict(opt=opt, statees=states, times=times, temps=temps,
                plots=plots, viols=viols, proc=proc)

def get_state0_cmd_tlm(db, tstart):
    """Get initial state and temps at time ``tstart`` using telemetry and
    cmd_states database table
    """
    tlm = get_telem_values(tstart, ['1pdeaat', '1pin1at'])
    state0 = {'T_dea': np.mean(tlm['1pdeaat']),
              'T_pin': np.mean(tlm['1pin1at']),
              'tstart': tlm[0]['date'],
              'tstop': tlm[-1]['date']}

    # Get commanded state containing tstop
    tstop = state0['tstop']
    sql = """SELECT * FROM cmd_states
             WHERE tstart <= %f AND tstop > %f
             ORDER BY tstart""" % (tstop, tstop)
    logging.debug('Running query\n%s\n' % sql)
    cmd_state = db.fetchone(sql)

    if cmd_state is None:
        raise ValueError("No commanded state found for %s.\n"
                         "Re-run specifying pitch, simpos, power, T_dea and T_pin."
                         % DateTime(tstop).date)
    else:
        # Update state0 from cmd_state, ignoring time keys
        for key in set(cmd_state) - set(('tstart', 'tstop', 'datestart', 'datestop')):
            state0[key] = cmd_state[key]

    return state0

def get_times_bs_cmds(opt):
    """Get tstart, tstop and bs_cmds depending on opt.oflsdir"""
    if opt.oflsdir:
        backstop_file = globfile(os.path.join(opt.oflsdir, 'CR*.backstop'))
        logging.debug('Using backstop file %s' % backstop_file)
        bs_cmds = Ska.ParseCM.read_backstop(backstop_file)
        tstart = bs_cmds[0]['time']
        tstop = bs_cmds[-1]['time']
        logging.debug('Found %d backstop commands between %s and %s' %
                      (len(bs_cmds), DateTime(tstart).date, DateTime(tstop)))
    else:
        if opt.tstart is None or opt.tstop is None:
            raise ValueError('Values for --tstart and --tstop are required')
        bs_cmds = []
        tstart = DateTime(opt.tstart).secs
        tstop = DateTime(opt.tstop).secs

    return tstart, tstop, bs_cmds

def get_cmds(db, datestart, datestop):
    """
    Get commanded states starting from ``state0`` and ending at time ``tstop``
    using a combination of the cmd_states database table and the supplied
    ``bs_cmds`` backstop commands.
    """
    # Get commands after the initial state0 and befofre datestop
    sql = """SELECT * FROM commands
             WHERE datestart >= '%s' and datestart < '%s'
             ORDER BY datestart""" % (datestart, datestop)
    logging.debug('Running query\n%s\n' % sql)
    cmds = db.fetchall(sql)
        
    logging.debug('Found %d commands from %s to %s' % (len(cmds), datestart, datestop))
    return cmds

def get_telem_values(tstart, colspecs):
    """
    Get most recent available telemetry state before time ``tstart``.

    :param tstart: desired time for state
    :rtype: state dictionary
    """

    # Fetch a day of telemetry before tstart.  Step back by a day if nothing found.
    delta_days = 0
    while True:
        start = DateTime(tstart - (delta_days + 1) * 86400).date
        stop = DateTime(tstart - delta_days * 86400).date
        logging.debug('Fetching telemetry between %s and %s' % (start, stop))
        colnames, vals = Ska.TelemArchive.fetch.fetch(start=start,
                                                      stop=stop,
                                                      colspecs=colspecs)

        # Finished when we found at least 10 good records (5 mins)
        if len(vals) > 10:
            logging.debug('Found %d values' % len(vals))
            break
        if delta_days > 100:
            raise ValueError('Found no telemetry within 100 days of %s' % str(tstart))

        delta_days += 1

    return np.rec.fromrecords(vals[-10:], names=colnames)

def rst_to_html(opt, proc):
    """Run rst2html.py to render index.rst as HTML"""

    # First copy CSS files to outdir
    import docutils.writers.html4css1
    dirname = os.path.dirname(docutils.writers.html4css1.__file__)
    shutil.copy2(os.path.join(dirname, 'html4css1.css'), opt.outdir)

    dirname = os.path.dirname(__file__)
    shutil.copy2(os.path.join(dirname, 'psmc_check.css'), opt.outdir)

    spawn = Ska.Shell.Spawn(stdout=None)
    infile = os.path.join(opt.outdir, 'index.rst')
    outfile = os.path.join(opt.outdir, 'index.html')
    status = spawn.run(['rst2html.py',
                        '--stylesheet-path=%s' % os.path.join(opt.outdir, 'psmc_check.css'),
                        infile, outfile])
    if status != 0:
        proc['errors'].append('rst2html.py failed with status %d: check run log.' % status)
        logging.error('rst2html.py failed')
        logging.error(''.join(spawn.outlines) + '\n')

    # Remove the stupid <colgroup> field that docbook inserts.  This
    # <colgroup> prevents HTML table auto-sizing.
    del_colgroup = re.compile(r'<colgroup>.*?</colgroup>', re.DOTALL)
    outtext = del_colgroup.sub('', open(outfile).read())
    open(outfile, 'w').write(outtext)

def config_logging(opt):
    loglevels = {0: logging.CRITICAL, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(level= loglevels.get(opt.verbose, logging.INFO),
                        format= '%(message)s',
                        filename= os.path.join(opt.outdir, 'run.dat'),
                        filemode= 'w',)

def write_states(opt, states):
    """Write states recarray to file states.dat"""
    out = open(os.path.join(opt.outdir, 'states.dat'), 'w')
    fmt = {'power': '%.1f',
           'pitch': '%.2f',
           'tstart': '%.2f',
           'tstop': '%.2f',
           }
    Ska.Numpy.pprint(states, fmt, out)
    out.close()

def write_temps(opt, times, temps):
    """Write temperature predictions to file temperatures.dat"""
    T_dea = temps['dea']
    T_pin = temps['pin']
    temp_recs = [(times[i], DateTime(times[i]).date, T_dea[i], T_pin[i]) for i in xrange(len(times))]
    temp_array = np.rec.fromrecords(temp_recs, names=('time', 'date', '1pdeaat', '1pin1at'))

    fmt = {'1pin1at': '%.2f',
           '1pdeaat': '%.2f',
           'time': '%.2f'}
    out = open(os.path.join(opt.outdir, 'temperatures.dat'), 'w')
    Ska.Numpy.pprint(temp_array, fmt, out)
    out.close()

def write_index_rst(opt, plots, viols, proc):
    """
    Make output text (in ReST format) in opt.outdir.
    """
    django_context = django.template.Context({'opt': opt,
                                              'plots': plots,
                                              'viols': viols,
                                              'proc': proc,
                                              })
    index_template = open('index_template.rst').read()
    index_template = re.sub(r' %}\n', ' %}', index_template)
    template = django.template.Template(index_template)
    outfile = open(os.path.join(opt.outdir, 'index.rst'), 'w') if opt.outdir else sys.stdout
    print >>outfile, template.render(django_context)

def make_viols(opt, states, times, temps):
    """
    Find limit violations where predicted temperature is above the
    yellow limit minus margin.
    """
    viols = dict((x, []) for x in MSID)
    for msid in MSID:
        temp = temps[msid]
        bad = np.concatenate(([False],
                             temp >= YELLOW[msid] - MARGIN[msid],
                             [False]))
        changes = np.flatnonzero(bad[1:] != bad[:-1]).reshape(-1, 2)

        for change in changes:
            viols[msid].append({'datestart': DateTime(times[change[0]]).date,
                                'datestop': DateTime(times[change[1]-1]).date,
                                'maxtemp': temp[change[0]:change[1]].max()
                                })
    return viols

def plot_two(fig_id, x, y, x2, y2,
             linestyle='-', linestyle2='-',
             color='blue', color2='magenta',
             ylim=None, ylim2=None,
             xlabel='', ylabel='', ylabel2='', title='',
             figsize=(7,3.5),
             ):
    """Plot two quantities with a date x-axis"""
    xt = Ska.Matplotlib.cxctime2plotdate(x)
    fig = plt.figure(fig_id, figsize=figsize)
    fig.clf()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot_date(xt, y, fmt='-', linestyle=linestyle, color=color)
    ax.set_xlim(min(xt), max(xt))
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    ax2 = ax.twinx()

    xt2 = Ska.Matplotlib.cxctime2plotdate(x2)
    ax2.plot_date(xt2, y2, fmt='-', linestyle=linestyle2, color=color2)
    ax2.set_xlim(min(xt), max(xt))
    if ylim2:
        ax2.set_ylim(*ylim2)
    ax2.set_ylabel(ylabel2, color=color2)
    ax2.xaxis.set_visible(False)

    ticklocs = Ska.Matplotlib.set_time_ticks(ax)
    [label.set_rotation(30) for label in ax.xaxis.get_ticklabels()]
    [label.set_color(color2) for label in ax2.yaxis.get_ticklabels()]

    fig.subplots_adjust(bottom=0.22)
    plt.draw()

    return {'fig': fig, 'ax': ax, 'ax2': ax2}

def make_plots(opt, states, times, temps):
    """
    Make output plots.
    
    :param opt: options
    :param states: commanded states
    :param times: time stamps (sec) for temperature arrays
    :param T_pin: 1pin1at temperatures
    :param T_dea: 1pddeat temperatures
    :rtype: dict of review information including plot file names
    """
    plots = {}
    
    for fig_id, msid in enumerate(('dea', 'pin')):
        plots[msid] = plot_two(fig_id=fig_id+1,
                               x=times,
                               y=temps[msid],
                               x2=pointpair(states['tstart'], states['tstop']),
                               y2=pointpair(states['pitch']),
                               title=MSID[msid],
                               xlabel='Date',
                               ylabel='Temperature (C)',
                               ylabel2='Pitch (deg)',
                               ylim2=(40, 180),
                               )
        plots[msid]['ax'].axhline(YELLOW[msid], linestyle='-', color='b')
        plots[msid]['ax'].axhline(YELLOW[msid] - MARGIN[msid], linestyle='--', color='b')
        plt.draw()
        if opt.outdir:
            filename = MSID[msid].lower() + '.png'
            plots[msid]['fig'].savefig(os.path.join(opt.outdir, filename))
            plots[msid]['filename'] = filename

    plots['pow_sim'] = plot_two(fig_id=3,
                                title='PSMC power and SIM-Z position',
                                xlabel='Date',
                                x=pointpair(states['tstart'], states['tstop']),
                                y=pointpair(states['power']),
                                ylabel='Power (watts)',
                                ylim=(0, 160.),
                                x2=pointpair(states['tstart'], states['tstop']),
                                y2=pointpair(states['simpos']),
                                ylabel2='SIM-Z (steps)',
                                ylim2=(-105000, 105000),
                           )
    plots['pow_sim']['fig'].subplots_adjust(right=0.85)
    plt.draw()
    if opt.outdir:
        filename = 'pow_sim.png'
        plots['pow_sim']['fig'].savefig(os.path.join(opt.outdir, filename))
        plots['pow_sim']['filename'] = filename

    return plots

def get_telem_state(tstart, colspecs):
    """
    Get most recent available telemetry state before time ``tstart``.

    :param tstart: desired time for state
    :rtype: state dictionary
    """

    # Fetch a day of telemetry before tstart.  Step back by a day if nothing found.
    delta_days = 0
    while True:
        start = DateTime(tstart - (delta_days + 1) * 86400).date
        stop = DateTime(tstart - delta_days * 86400).date
        logging.debug('Fetching telemetry between %s and %s' % (start, stop))
        colnames, vals = Ska.TelemArchive.fetch.fetch(start=start,
                                                      stop=stop,
                                                      colspecs=colspecs['1pin1at', '1pdeaat',
                                                                'tscpos',
                                                                'point_suncentang',
                                                                '1de28avo', '1deicacu', '1dp28avo',
                                                                '1dpicacu', '1dp28bvo', '1dpicbcu',
                                                                'aoattqt1', 'aoattqt2', 'aoattqt3', 'aoattqt4', ])

        # Finished when we found at least 10 good records (5 mins)
        if len(vals) > 10:
            logging.debug('Found %d values' % len(vals))
            break
        if delta_days > 100:
            raise ValueError('Found no telemetry within 100 days of %s' % str(tstart))

        delta_days += 1

    tlm = np.rec.fromrecords(vals[-10:], names=colnames)
    state0 = {'power': np.mean(tlm['1de28avo'] * tlm['1deicacu'] +
                               tlm['1dp28avo'] * tlm['1dpicacu'] +
                               tlm['1dp28bvo'] * tlm['1dpicbcu']),
              'T_dea': np.mean(tlm['1pdeaat']),
              'T_pin': np.mean(tlm['1pin1at']),
              'pitch': tlm[-1]['point_suncentang'],
              'simpos': tlm[-1]['tscpos'],
              'tstart': tlm[0]['date'],
              'tstop': tlm[-1]['date'],
              'q1': tlm[-1]['aoattqt1'],
              'q2': tlm[-1]['aoattqt2'],
              'q3': tlm[-1]['aoattqt3'],
              'q4': tlm[-1]['aoattqt4'],
              }

    return state0

def get_power(states):
    """
    Determine the power value in each state by finding the entry in calibration
    power table with the same ``fep_count``, ``vid_board``, and ``clocking``
    values.

    :param states: input states
    :rtype: numpy array of power corresponding to states
    """

    # Make a tuple of values that define a unique power state
    powstate = lambda x: tuple(x[col] for col in ('fep_count', 'vid_board', 'clocking'))

    # psmc_power charactestic is a list of 4-tuples (fep_count vid_board
    # clocking power_avg).  Build a dict to allow access to power_avg for
    # available (fep_count vid_board clocking) combos.
    power_states = dict((row[0:3], row[3]) for row in characteristics.psmc_power)
    try:
        powers = [power_states[powstate(x)] for x in states]
    except KeyError:
        raise ValueError('Unknown power state: %s' % str(powstate(x)))

    return powers

def pointpair(x, y=None):
    if y is None:
        y = x
    return np.array([x, y]).reshape(-1, order='F')

def etc():
    # build the model data
    T_pin, T_dea = twodof.calc_twodof_model(staterec, pin0, dea0, times)


    # plot it
    from Chandra.Time import DateTime
    date0 = DateTime(tstart)
    date1 = DateTime(tstop)

    date2009 = DateTime('2009:001:00:00:00')
    doy = (times - date2009.secs)/86400.0
    ok = (times >= date0.secs) & (times < date1.secs)
    doyok = doy[ok]
    figure(1, figsize=(6,9))
    clf()




    subplot(5, 1, 1)
    plot(doyok, tlm['1pdeaat'][ok])
    plot(doyok, T_dea[ok])
    ylabel('1pdeaat')
    xlimits = xlim()

    subplot(5, 1, 2)
    plot(doyok, tlm['1pdeaat'][ok] - T_dea[ok])
    ylabel('Resid')
    xlim(xlimits)

    subplot(5, 1, 3)
    statesok = staterec[ (staterec.tstop > date0.secs) & (staterec.tstart < date1.secs) ]
    statesdoy = (pointpair(statesok.tstart, statesok.tstop) - date2009.secs) / 86400.
    plot(doyok, pwr_smooth[ok])
    plot(statesdoy, pointpair(statesok.power), 'r')
    ylabel('Power')
    xlim(xlimits)

    subplot(5, 1, 4)
    plot(doyok, tlm['point_suncentang'][ok])
    plot(statesdoy, pointpair(statesok.pitch), 'r')
    ylabel('Pitch')
    xlim(xlimits)

    subplot(5, 1, 5)
    plot(doyok, tlm['tscpos'][ok]/1000.)
    plot(statesdoy, pointpair(statesok.simpos/1000.), 'r')
    ylabel('SIM-Z')
    xlabel('Day of Year in 2009')
    xlim(xlimits)
    #savefig('model_2008-%02d.png' % month)

def globfile(pathglob):
    """Return the one file name matching ``pathglob``.  Zero or multiple
    matches raises an IOError exception."""

    files = glob.glob(pathglob)
    if len(files) == 0:
        raise IOError('No files matching %s' % pathglob)
    elif len(files) > 1:
        raise IOError('Multiple files matching %s' % pathglob)
    else:
        return files[0]

if __name__ == '__main__':
    opt, args = get_options()
    try:
        main(opt)
    except Exception, msg:
        if opt.traceback:
            raise
        else:
            print "ERROR:", msg
            sys.exit(1)
