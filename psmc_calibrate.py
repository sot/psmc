#!/usr/bin/env python

"""
Calibrate PSMC model coefficients using telemetry from specified time range.
"""

import sys
import time
import optparse

import matplotlib.pyplot as plt
import Chandra.Time
import numpy as np
import twodof
import Ska.Table
import Ska.DBI
import psmc_check
import characteristics

from sherpa.astro.ui import *
from sherpa.stats import *
from sherpa.optmethods import *
from sherpa.estmethods import *


PARNAMES = sorted(characteristics.model_par)

def psmc_temps_model(msid, tlm, states):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    cache = dict(pars=None)

    def psmc_temp(pars, times):
        par = dict(zip(PARNAMES, pars))
        if pars != cache['pars']:
            cache['1pin1at'], cache['1pdeaat'] = \
                twodof.calc_twodof_model(states,
                                         tlm[0]['1pin1at'], tlm[0]['1pdeaat'],
                                         times, dt=300.0,
                                         par=par)
            cache['pars'] = pars
            print pars
        return cache[msid]

    return psmc_temp

def psmc_temps_model_multi(msid, tlm, states, n_core):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    from multiprocessing import Process, Pipe
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

    import os
    def twodof_multi(conn):
        while True:
            par = conn.recv()
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
        parent_conn, child_conn = Pipe()
        p = Process(target=twodof_multi,
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
        par = dict(zip(PARNAMES, pars))
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
            # print msid, pars

        return cache[msid]

    return psmc_temp

def get_tlm_states(datestop='2009-06-01T00:00:00', ndays=180):
    datestop = Chandra.Time.DateTime(datestop)

    print 'Fetching telemetry for %d days before %s' % (ndays, datestop.date)
    tlm = psmc_check.get_telem_values(datestop.date,
                                      ['1pdeaat', '1pin1at'],
                                      days=ndays, dt=300)

    print 'Getting states between %s : %s' % (tlm[0].date, tlm[-1].date)
    db = Ska.DBI.DBI(dbi='sybase', user='aca_read')
    states = psmc_check.get_states(tlm[0].date, tlm[-1].date, db)
    # Calc state values at tlm times
    indexes = np.searchsorted(states.tstop, tlm['date'])
    statevals = states[indexes]

    return tlm, states, statevals

def init_models_data(tlm, states, model_par, n_core):
    staterror = {'1pdeaat' : 1.0,
                 '1pdeabt' : 4.0,
                 '1pin1at' : 1.0}

    ones = np.ones_like(tlm.date)

    print "Setting dataset 1 = 1pdeaat"
    load_arrays(1, tlm.date, tlm['1pdeaat'], staterror['1pdeaat'] * ones, Data1D)
    dat1 = get_data(1)

    print "Setting dataset 2 = 1pin1at"
    load_arrays(2, tlm.date, tlm['1pin1at'], staterror['1pin1at'] * ones, Data1D)
    dat2 = get_data(2)

    T_dea0 = dat1.y[0]
    T_pin0 = dat2.y[0]

    if n_core > 0:
        dea_temps = psmc_temps_model_multi('1pdeaat', tlm, states, n_core)
        pin_temps = psmc_temps_model_multi('1pin1at', tlm, states, n_core)
    else:
        dea_temps = psmc_temps_model('1pdeaat', tlm, states)
        pin_temps = psmc_temps_model('1pin1at', tlm, states)

    set_stat('chi2gehrels')

    load_user_model(dea_temps, 'dea')
    load_user_model(pin_temps, 'pin')
    add_user_pars('dea', PARNAMES)
    add_user_pars('pin', PARNAMES)

    set_model(1, dea)
    set_model(2, pin)

    for parname in PARNAMES:
        setattr(dea, parname, model_par[parname])
        setattr(pin, parname, getattr(dea, parname))

    return dea, pin, dat1, dat2

def print_model_par():
    print 'model_par = dict('
    for parname in PARNAMES:
        print " "*17 + '%-7s = %7.3f,' % (parname, getattr(dea, parname).val)
    print '                )'

def save_fit_figures(root, dat1, statevals):
    print 'Residuals'
    plt.figure(figsize=(8,4))
    plot_fit_resid(1)

    plt.xlabel('Time (seconds)')
    plt.ylabel('Temperature (degC)')
    plt.title('Fit and residuals (data - model)')
    plt.savefig(root + 'fit_resid.png')

    mp = get_model_plot()
    print 'Histogram'
    plt.figure(figsize=(5.5, 4))
    plt.hist(dat1.y - mp.y, bins=30)

    plt.xlabel('Fit residuals (data - model)')
    plt.title('Fit residual distribution (degC)')

    plt.savefig(root + 'fit_resid_hist.png')

    plt.figure(figsize=(5.5, 4))
    print 'Scatter'
    plt.plot(dat1.y + np.random.uniform(-1.25, 1.25, len(dat1.y)), dat1.y - mp.y, '.')
    plt.xlabel('Temperature (degC from telemetry)')
    plt.ylabel('Residual (data-model) (degC)')
    plt.title('Fit residual vs. temperature')
    plt.savefig(root + 'fit_resid_vs_temp.png')

    plt.figure(figsize=(5.5, 4))
    print 'Scatter2'
    t0 = time.time()
    plt.plot(statevals['simpos'] + np.random.uniform(-5000, 5000, len(statevals['simpos'])),
              statevals['pitch'], '.')
    t1 = time.time(); print t1-t0
    plt.xlabel('SIM-Z (counts)')
    plt.ylabel('Pitch (degrees)')
    plt.title('Data coverage (each dot = 32 sec)')
    t1 = time.time(); print t1-t0
    plt.savefig(root + 'fit_pitch_simpos.png')
    t1 = time.time(); print t1-t0

def fitall():
    for detector in ('hrci', 'acis', 'hrcs'):
        for pitch in ('50', '90', '150'):
            thaw(getattr(dea, detector + pitch))
        print 'Fitting', detector, 'settling temps at', time.ctime()
        fit(1,2)
        freeze(dea)
        print 'Done at', time.ctime()

    thaw(dea.u01)
    thaw(dea.u12)
    thaw(dea.c1)
    thaw(dea.c2)
    # thaw(dea.u01quad)
    print 'Fitting time const params at', time.ctime()
    fit(1,2)
    freeze(dea)
    print 'Done at', time.ctime()

    plot_fit_resid(1)
    print dea
    

def fitdea():
    for detector in ('acis', 'hrcs', 'hrci'):
        for pitch in ('50', '90', '150'):
            thaw(getattr(dea, detector + pitch))
        print 'Fitting', detector, 'settling temps at', time.ctime()
        fit(1)
        freeze(dea)
        print 'Done at', time.ctime()

    thaw(dea.u01)
    thaw(dea.u12)
    thaw(dea.c1)
    thaw(dea.c2)
    thaw(dea.u01quad)
    print 'Fitting time const params at', time.ctime()
    fit(1)
    freeze(dea)
    print 'Done at', time.ctime()

    plot_fit_resid(1)
    print dea

def killall():
    import multiprocessing
    for p in multiprocessing.active_children():
        p.terminate()

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
                      default=360,
                      help="Number of days for HRC")
    parser.add_option('--figroot',
                      default='',
                      help="Figure root name")
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
    return parser.parse_args()
        
def main():
    global opt
    opt, args = get_options()

    if opt.datestop is None:
        opt.datestop = Chandra.Time.DateTime(time.time()-7*86400, format='unix').date
        print 'Datestop =', opt.datestop

    set_method('simplex')
    get_method().config.update(dict(ftol=1e-3,
                         finalsimplex=0,
                         maxfev=2000))

    # Fit HRC-I and HRC-S (typically for a longer period such as 365 days)
    model_par = characteristics.model_par
    tlm, states, statevals = get_tlm_states(opt.datestop, opt.ndays_hrc)
    dea, pin, dat1, dat2 = init_models_data(tlm, states, model_par, opt.n_core)

    print 'Original model pars:'
    print_model_par()

    freeze(dea)
    for detector in ('hrci', 'hrcs'):
        for pitch in ('50', '90', '150'):
            thaw(getattr(dea, detector + pitch))

    print 'Fitting HRC-S and HRC-I settling temps at', time.ctime()
    if opt.fit:
        fit(1,2)
    freeze(dea)
    print 'Done at', time.ctime()

    for parname in PARNAMES:
        model_par[parname] = getattr(dea, parname).val

    # Fit ACIS-I and ACIS-S and time constants (typically for a shorter period
    # such as 180 days).  This is because ACIS has more coverage and may vary faster.
    tlm, states, statevals = get_tlm_states(opt.datestop, opt.ndays_acis)
    dea, pin, dat1, dat2 = init_models_data(tlm, states, model_par, opt.n_core)
    
    freeze(dea)
    for pitch in ('50', '90', '150'):
        thaw(getattr(dea, 'acis' + pitch))
    thaw(dea.u01)
    thaw(dea.u12)
    thaw(dea.c1)
    thaw(dea.c2)
    freeze(dea.u01quad)

    print 'Fitting ACIS-I, ACIS-S and time constants at', time.ctime()
    if opt.fit:
        fit(1,2)
    freeze(dea)
    print 'Done at', time.ctime()

    for parname in PARNAMES:
        model_par[parname] = getattr(dea, parname).val

    save_fit_figures(opt.figroot, dat1, statevals)
    print_model_par()
    if opt.n_core > 0:
        print 'Killing processes'
        killall()
    print 'Goodbye'

if __name__ == '__main__':
    main()

# Example code for cut-n-paste if running interactively
"""
if 'datestop' not in globals():
    datestop = '2009-06-01T00:00:00'
if 'ndays' not in globals():
    ndays = 30
tlm, states, statevals = get_tlm_states(datestop, ndays)
dea, pin, dat1, dat2 = init_models_data(tlm, states)
plot_fit_resid(1)
"""
