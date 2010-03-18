#!/usr/bin/env python

"""
Calibrate PSMC model coefficients using telemetry from specified time range.
"""

import sys
import os
import time
import optparse
import json
import contextlib
import shutil
import hg
import multiprocessing

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import Chandra.Time
import numpy as np
import twodof
import Ska.Table
import Ska.DBI
import psmc_check
import characteristics
import logging
import clogging
import sherpa.ui as ui

def psmc_temps_model(msid, tlm, states, model_pars):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    cache = dict(pars=None)
    par_names = sorted(model_pars)

    def psmc_temp(pars, times):
        par = dict(zip(par_names, pars))
        if pars != cache['pars']:
            cache['1pin1at'], cache['1pdeaat'] = \
                twodof.calc_twodof_model(states,
                                         tlm[0]['1pin1at'], tlm[0]['1pdeaat'],
                                         times, dt=300.0,
                                         par=par)
            cache['pars'] = pars
            logger.info(str(pars))
        return cache[msid]

    return psmc_temp

def psmc_temps_model_multi(msid, tlm, states, n_core, model_pars):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    core_tstarts = np.linspace(tlm[0].date, tlm[-1].date, n_core+1)

    # Divide the states up into n_core pieces.  Force the start/end values
    # to be as expected.
    s_idxs = np.searchsorted(states['tstop'], core_tstarts)
    s_idxs[0] = 0
    s_idxs[-1] = len(states)
    core_states = [states[s_idxs[i]:s_idxs[i+1]] for i in range(n_core)]
    core_tstarts = [core_states[i][0].tstart for i in range(n_core)]

    # Divide the times into the same intervals as the core_states and again
    # force the start/end values to be correct.
    t_idxs = np.searchsorted(tlm.date, core_tstarts)
    t_idxs[0] = 0
    t_idxs = np.append(t_idxs, [len(tlm.date)])
    core_times = [tlm.date[t_idxs[i]:t_idxs[i+1]] for i in range(n_core)]
    par_names = sorted(model_pars)

    import os
    def twodof_multi(conn):
        while True:
            par = conn.recv()
            if par is None:
                sys.exit(0)

            pin, dea = twodof.calc_twodof_model(states=core_states[i],
                                                T_pin0=tlm['1pin1at'][t_idxs[i]],
                                                T_dea0=tlm['1pdeaat'][t_idxs[i]],
                                                times=core_times[i],
                                                dt=300.0,
                                                par=par)
            conn.send((pin, dea))

    conns = []
    ps = []
    for i in range(n_core):
        parent_conn, child_conn = multiprocessing.Pipe()
        p = multiprocessing.Process(target=twodof_multi,
                    args=(child_conn,))
        p.start()
        ps.append(p)
        conns.append(parent_conn)

    cache = dict(pars=None)
    def psmc_temp(pars, times):
        """Evalate the twodof model for ``pars`` at ``times``.

        For efficiency the supplied ``times`` is ignored since it must be the
        same as tlm.date used above which was used to create core_times.
        """
        if pars is None:
            for conn in conns:
                conn.send(None)
            return
        
        par = dict(zip(par_names, pars))
        if pars != cache['pars']:
            pins = []
            deas = []
            # Start the cores in parallel by supplying par values
            for i in range(n_core):
                conns[i].send(par)

            # Get the return values
            for i in range(n_core):
                pin, dea = conns[i].recv()
                pins.append(pin)
                deas.append(dea)
                
            cache['1pdeaat'] = np.hstack(deas)
            cache['1pin1at'] = np.hstack(pins)
            cache['pars'] = pars
            print '.',
            sys.stdout.flush()

        return cache[msid]

    return psmc_temp

def my_stat_func(data, model, staterror, syserror=None, weight=None):
    warm = data > 35
    staterror = np.ones_like(data) 
    staterror[warm] /= (1.0 + (data[warm] - 35.0) / 5.0)**2

    stat = np.sum((data-model)**2 / staterror)
    print 'stat=', stat
    return stat, staterror

def my_staterr_func(data):
    raise Exception
    return staterror

def get_tlm_states(datestop='2009-06-01T00:00:00', ndays=180):
    datestop = Chandra.Time.DateTime(datestop)

    logger.info('Fetching telemetry for %d days before %s' % (ndays, datestop.date))
    tlm = psmc_check.get_telem_values(datestop.date,
                                      ['1pdeaat', '1pin1at'],
                                      days=ndays, dt=300)

    logger.info('Getting states between %s : %s' % (tlm[0].date, tlm[-1].date))
    db = Ska.DBI.DBI(dbi='sybase')
    states = psmc_check.get_states(tlm[0].date, tlm[-1].date, db)
    # Calc state values at tlm times
    indexes = np.searchsorted(states.tstop, tlm['date'])
    statevals = states[indexes]

    return tlm, states, statevals

def init_models_data(tlm, states, model_pars, n_core):
    staterror = {'1pdeaat' : 1.0,
                 '1pdeabt' : 4.0,
                 '1pin1at' : 1.0}

    ones = np.ones_like(tlm.date)
    par_names = sorted(model_pars)

    logger.info("Setting dataset 1 = 1pdeaat")
    ui.load_arrays(1, tlm.date, tlm['1pdeaat'], staterror['1pdeaat'] * ones, ui.Data1D)
    dat1 = ui.get_data(1)

    logger.info("Setting dataset 2 = 1pin1at")
    ui.load_arrays(2, tlm.date, tlm['1pin1at'], staterror['1pin1at'] * ones, ui.Data1D)
    dat2 = ui.get_data(2)

    T_dea0 = dat1.y[0]
    T_pin0 = dat2.y[0]

    if n_core > 0:
        dea_temps = psmc_temps_model_multi('1pdeaat', tlm, states, n_core, model_pars)
        pin_temps = psmc_temps_model_multi('1pin1at', tlm, states, n_core, model_pars)
    else:
        dea_temps = psmc_temps_model('1pdeaat', tlm, states, model_pars)
        pin_temps = psmc_temps_model('1pin1at', tlm, states, model_pars)

    # ui.set_stat('chi2gehrels')

    ui.load_user_model(dea_temps, 'dea')
    ui.load_user_model(pin_temps, 'pin')
    ui.add_user_pars('dea', par_names)
    ui.add_user_pars('pin', par_names)

    ui.set_model(1, dea)
    ui.set_model(2, pin)

    for parname in par_names:
        setattr(dea, parname, model_pars[parname])
        setattr(pin, parname, getattr(dea, parname))

    return dea, pin, dat1, dat2

def print_model_pars(par_names):
    logger.info('model_pars = dict(')
    for parname in par_names:
        logger.info(" "*17 + '%-7s = %7.3f,' % (parname, getattr(dea, parname).val))
    logger.info('                )')

def save_fit_figures(root, dat1, statevals):
    plt.figure(figsize=(8,4))
    ui.plot_fit_resid(1)

    plt.xlabel('Time (seconds)')
    plt.ylabel('Temperature (degC)')
    plt.title('Fit and residuals (data - model)')
    plt.savefig(os.path.join(root, 'fit_resid.png'))

    mp = ui.get_model_plot()
    plt.figure(figsize=(5.5, 4))
    plt.hist(dat1.y - mp.y, bins=30)

    plt.xlabel('Fit residuals (data - model)')
    plt.title('Fit residual distribution (degC)')

    plt.savefig(os.path.join(root, 'fit_resid_hist.png'))

    plt.figure(figsize=(5.5, 4))
    plt.plot(dat1.y + np.random.uniform(-1.25, 1.25, len(dat1.y)), dat1.y - mp.y, '.')
    plt.xlabel('Temperature (degC from telemetry)')
    plt.ylabel('Residual (data-model) (degC)')
    plt.title('Fit residual vs. temperature')
    plt.savefig(os.path.join(root, 'fit_resid_vs_temp.png'))

    plt.figure(figsize=(5.5, 4))
    t0 = time.time()
    plt.plot(statevals['simpos'] + np.random.uniform(-5000, 5000, len(statevals['simpos'])),
              statevals['pitch'], '.')
    plt.xlabel('SIM-Z (counts)')
    plt.ylabel('Pitch (degrees)')
    plt.title('Data coverage (each dot = 32 sec)')
    plt.savefig(os.path.join(root, 'fit_pitch_simpos.png'))

def killall():
    for p in multiprocessing.active_children():
        print 'Terminating', p.pid, 'with alive=', p.is_alive()
        p.terminate()
        time.sleep(1)
        print 'Status for process', p.pid, 'is alive=', p.is_alive()

def get_options():
    parser = optparse.OptionParser()
    parser.add_option("--datestop",
                      default=None,
                      help="Stop date for calibration dataset")
    parser.add_option("--ndays-acis",
                      type='int',
                      default=180,
                      help="Number of days for ACIS")
    parser.add_option("--ndays-hrc",
                      type='int',
                      default=240,
                      help="Number of days for HRC")
    parser.add_option('--data-dir',
                      default=os.path.join(os.path.dirname(__file__), 'fit'),
                      help="Data files root directory")
    parser.add_option('--fit',
                      action='store_true',
                      default=True,
                      help="Do fitting")
    parser.add_option('--no-fit',
                      action='store_false',
                      dest='fit',
                      help="Do not do fitting")
    parser.add_option('--n-core',
                      type='int',
                      default=0,
                      help="Number of multiprocessing cores (default=0 => no multiprocessing)")
    parser.add_option('--pars-file',
                      default='model_pars.json',
                      help="Model parameters file name")
    parser.add_option('--hg-commit',
                      action='store_true',
                      default=False,
                      help="Commit to hg repository after generating new model pars")
    parser.add_option('--quiet',
                      action='store_true',
                      help="Suppress stdout output")
    return parser.parse_args()
        
def config_logger(logfile, quiet):
    logger = clogging.config_logger('calibrate', level=clogging.INFO, filename=logfile,
                                    stream=(None if quiet else sys.stdout))
    sherpa_logger = logging.getLogger('sherpa')
    for h in sherpa_logger.handlers:
        sherpa_logger.removeHandler(h)
    for h in logger.handlers:
        sherpa_logger.addHandler(h)
    return logger

def main():
    global logger
    global opt
    opt, args = get_options()

    pars_file_name = os.path.join(opt.data_dir, opt.pars_file)
    if not os.path.exists(opt.data_dir):
        os.makedirs(opt.data_dir)
        shutil.copy2(os.path.join(os.path.dirname(__file__), opt.pars_file), pars_file_name)

    logger = config_logger(os.path.join(opt.data_dir, 'log'), opt.quiet)

    model_pars = json.load(open(pars_file_name))
    par_names = sorted(model_pars)

    if opt.datestop is None:
        opt.datestop = Chandra.Time.DateTime(time.time()-4*86400, format='unix').date
        logger.info('Datestop = %s', opt.datestop)

    ui.set_method('simplex')
    ui.get_method().config.update(dict(ftol=1e-3,
                                       finalsimplex=0,
                                       maxfev=2000))

    ui.load_user_stat("mystat", my_stat_func, my_staterr_func)
    ui.set_stat(mystat)

    # Fit HRC-I and HRC-S (typically for a longer period such as 365 days)
    tlm, states, statevals = get_tlm_states(opt.datestop, opt.ndays_hrc)
    dea, pin, dat1, dat2 = init_models_data(tlm, states, model_pars, opt.n_core)

    logger.info('Original model pars:')
    print_model_pars(par_names)

    ui.freeze(dea)
    for detector in ('hrci', 'hrcs'):
        for pitch in ('50', '90', '150'):
            ui.thaw(getattr(dea, detector + pitch))

    logger.info('Fitting HRC-S and HRC-I settling temps at %s', time.ctime())
    if opt.fit:
        ui.fit(1, 2)
    ui.freeze(dea)
    logger.info('Done at %sn', time.ctime())

    for parname in par_names:
        model_pars[parname] = getattr(dea, parname).val

    if opt.n_core > 0:
        dea.calc(None, None)
        pin.calc(None, None)

    # Fit ACIS-I and ACIS-S and time constants (typically for a shorter period
    # such as 180 days).  This is because ACIS has more coverage and may vary faster.
    tlm, states, statevals = get_tlm_states(opt.datestop, opt.ndays_acis)
    dea, pin, dat1, dat2 = init_models_data(tlm, states, model_pars, opt.n_core)
    
    ui.freeze(dea)
    for detector in ('acis', ):
        for pitch in ('50', '90', '150'):
            ui.thaw(getattr(dea, detector + pitch))
    ui.thaw(dea.u01)
    ui.thaw(dea.u12)
    ui.thaw(dea.c1)
    ui.thaw(dea.c2)
    ui.freeze(dea.u01quad)

    logger.info('Fitting ACIS-I, ACIS-S and time constants at %s', time.ctime())
    if opt.fit:
        ui.fit(1, 2)
    ui.freeze(dea)
    logger.info('Done at %s', time.ctime())

    for parname in par_names:
        model_pars[parname] = getattr(dea, parname).val

    save_fit_figures(opt.data_dir, dat1, statevals)
    print_model_pars(par_names)
    json.dump(model_pars, open(pars_file_name, 'w'), indent=4, sort_keys=True)

    if opt.n_core > 0:
        dea.calc(None, None)
        pin.calc(None, None)
    
    logger.info('Goodbye')
    for h in logger.handlers:
        h.close()
    
    if opt.hg_commit:
        repo = hg.Hg(opt.data_dir, create=True)
        repo.commit(message=str(opt), date=hg.ctime_date(opt.datestop))

if __name__ == '__main__':
    main()
