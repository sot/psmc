import sys
import time

import Chandra.Time
import numpy as np
import twodof
import Ska.Table
import Ska.DBI
import psmc_check

from sherpa.stats import *
from sherpa.optmethods import *
from sherpa.estmethods import *
from sherpa.fit import Fit

parnames = sorted(twodof.pardefault)

def psmc_temps_model(msid, tlm, states):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    cache = dict(pars=None)

    def psmc_temp(pars, times):
        par = dict(zip(parnames, pars))
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

def psmc_temps_model_multi(msid, tlm, states):
    """Return a sherpa model to evaluate PSMC temperatures at given times."""
    from multiprocessing import Process, Pipe
    n_core = 4
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
        par = dict(zip(parnames, pars))
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
            print msid, pars

        return cache[msid]

    return psmc_temp

ndays = 180 # 90
date1 = Chandra.Time.DateTime('2009-04-01T00:00:00')

if 'tlm' not in globals():
    print 'Fetching telemetry for %d days before %s' % (ndays, date1.date)
    tlm = psmc_check.get_telem_values(date1.date,
                                      ['1pdeaat', '1pin1at'],
                                      days=ndays, dt=300)

if 'states' not in globals():
    print 'Getting states between %s : %s' % (tlm[0].date, tlm[-1].date)
    db = Ska.DBI.DBI(dbi='sybase')
    states = psmc_check.get_states(tlm[0].date, tlm[-1].date, db)

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

#dea_temps = psmc_temps_model('1pdeaat', tlm, states)
#pin_temps = psmc_temps_model('1pin1at', tlm, states)
dea_temps = psmc_temps_model_multi('1pdeaat', tlm, states)
pin_temps = psmc_temps_model_multi('1pin1at', tlm, states)

method = 'levmar'
set_stat('chi2gehrels')

load_user_model(dea_temps, 'dea')
load_user_model(pin_temps, 'pin')
add_user_pars('dea', parnames)
add_user_pars('pin', parnames)

set_model(1, dea)
set_model(2, pin)

for parname in parnames:
    setattr(dea, parname, twodof.pardefault[parname])
    setattr(pin, parname, getattr(dea, parname))

freeze(dea)

add_window(8, 4, 'inches')
plot_fit_resid(1)
print_window('fit_resid', ['format', 'png'])

mp = get_model_plot()
hy, hx = np.histogram(dat1.y - mp.y, bins=30)
add_window(5.5, 4, 'inches')
add_histogram(hx[:-1], hx[1:], hy)
print_window('fit_resid_hist', ['format', 'png'])

import numpy
add_window(5.5,4,'inches')
add_curve(dat1.y + np.random.uniform(-1.25, 1.25, len(dat1.y), dat1.y - mp.y)
ahelp('set_curve')
set_curve(['line.style', 'none', 'symbol.style', 'point'])

def fitall():
    for detector in ('acis', 'hrcs', 'hrci'):
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
    thaw(dea.u01quad)
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
        
