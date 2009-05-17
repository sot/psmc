import sys

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

def psmc_temps(msid):
    """Evaluate PSMC temperatures at given times."""
    def psmc_temp(pars, t):
        return twomass.calc_model(t, par=dict(zip(parnames, pars)), msid=msid)
    return psmc_temp

ndays = 60
date0 = Chandra.Time.DateTime('2009-02-01T00:00:00')
date1 = Chandra.Time.DateTime('2009-04-03T00:00:00')

if 'tlm' not in globals():
    print 'Fetching telemetry for %d days before %s' % (ndays, date1.date)
    tlm = psmc_check.get_telem_values(date1.date,
                                      ['1pdeaat', '1pin1at'],
                                      days=ndays, dt=300)

if 'states' not in globals():
    print 'Getting states between %s : %s' % (tlm[0].date, tlm[-1].date)
    db = Ska.DBI.DBI(dbi='sybase')
    states = psmc_check.get_states(tlm[0].date, tlm[-1].date, db)
    tstart = states[0].tstart
    tstop = states[-1].tstop
    states['tstart'] -= tstart
    states['tstop'] -= tstart

staterror = {'1pdeaat' : 1.0,
             '1pdeabt' : 4.0,
             '1pin1at' : 1.0}

ones = np.ones_like(tlm.date)

print "Setting dataset 1 = 1pdeaat"
load_arrays(1, tlm.date - tstart, tlm['1pdeaat'], staterror['1pdeaat'] * ones, Data1D)
dat1 = get_data(1)

print "Setting dataset 2 = 1pin1at"
load_arrays(2, tlm.date - tstart, tlm['1pin1at'], staterror['1pin1at'] * ones, Data1D)
dat2 = get_data(2)

T_dea0 = dat1.y[0]
T_pin0 = dat2.y[0]
twomass = twodof.TwoDOF(states, T_pin0, T_dea0)
dea_temps = psmc_temps('1pdeaat')
pin_temps = psmc_temps('1pin1at')

method = 'levmar'
set_stat('chi2gehrels')

load_user_model(psmc_temps('1pdeaat'), 'dea')
load_user_model(psmc_temps('1pin1at'), 'pin')
add_user_pars('dea', parnames)
add_user_pars('pin', parnames)

set_model(1, dea)
set_model(2, pin)

for parname in parnames:
    setattr(dea, parname, twodof.pardefault[parname])
    setattr(pin, parname, getattr(dea, parname))

freeze(dea)

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

    plot_fit_resid()

    print dea
