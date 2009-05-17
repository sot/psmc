import sys

if 'site-packages' not in sys.path:
    sys.path.append('site-packages')
import pkg_resources
pkg_resources.require('Chandra.Time', 'Ska.Table')

import Chandra.Time
import numpy as np
import twodof
import Ska.Table

from sherpa.stats import *
from sherpa.optmethods import *
from sherpa.estmethods import *
from sherpa.fit import Fit

class DeadChi( Stat ):
    """Calculate chi^2 but with a deadband"""
    deaderr2 = 50**2

    def __init__(self, name='deadchi'):  # , name='deadchi'
        Stat.__init__(self, name)

    @staticmethod
    def calc_staterror(data):
        return None

    @staticmethod
    def calc_stat( data, model, staterror=None, syserror=None, weight=None ):
        # print 'hello world'
        fvec = model - data
        d = abs(fvec)
        # syserror and staterr are used to pass the deadband size and intrinsic
        # (statistical) uncertainty, but they are always constant so just use
        # the first value.  (Sherpa needs these to be vectors, however). 
        deadband = 1.27
        staterr2 = staterror[0]**2
        out = d > deadband

        # Calculate fit statistic:
        #   Start with chi^2 = 1 per DOF
        #   Add a very shallow quadratic so chi^2 is not completely flat in deadband
        #   Add a strong error term as soon as the model is outside the deadband
        stat = ( len(data)               
                 + np.sum(d**2 / DeadChi.deaderr2)
                 + np.sum((d[out] - deadband)**2) / staterr2
                 )
        if 'CHI_DEBUG' in globals():
            print 'stat = %8.2f' % (stat)
        
        # stat = len(data) + np.sum((d[out] - syserror[out])**2 / staterror[out]**2)
        return stat, fvec

parnames = sorted(twodof.pardefault)
def psmc_temps(msid):
    """Evaluate PSMC temperatures at given times."""
    def psmc_temp(pars, t):
        return twomass.calc_model(t, msid=msid, par=dict(zip(parnames, pars)))
    return psmc_temp

if 'states08' not in globals():
    print 'Reading states08'
    states08 = Ska.Table.read_fits_table('2008_intervals.fits')

# Train period
#date0 = Chandra.Time.DateTime('2008-09-01T00:00:00')
#date1 = Chandra.Time.DateTime('2008-12-01T00:00:00')
date0 = Chandra.Time.DateTime('2008-04-08T00:00:00')
date1 = Chandra.Time.DateTime('2008-12-28T00:00:00')
states = states08[ (states08['tstart'] > date0.secs) & (states08['tstop'] < date1.secs) ]
tstart = states[0].tstart
tstop = states[-1].tstop
states['tstart'] -= tstart
states['tstop'] -= tstart

if 'tlm08' not in globals():
     tlm08 = Ska.Table.read_fits_table('telem_08.fits')
tlm = tlm08[ (tlm08['date'] > tstart) & (tlm08['date'] < tstop) ]

deadband = { '1pdeaat' : 1.27,
             '1pdeabt' : 1.27,
             '1pin1at' : .635}

staterror = {'1pdeaat' : 1.0,
             '1pdeabt' : 4.0,
             '1pin1at' : 1.0}

print "loading pdeaat"
load_data(1, 'telem_08.fits[cols date, 1pdeaat][date>%f][date<%f]' % (tstart, tstop))
dat1 = get_data(1)
dat1.x = dat1.x - tstart
dat1.staterror = staterror['1pdeaat'] * np.ones_like(dat1.x) # Set up pseudo statistical error 
# dat1.syserror = deadband[msid] * np.ones_like(dat1.x)


print "loading pin1at"
load_data(2, 'telem_08.fits[cols date, 1pin1at][date>%f][date<%f]' % (tstart, tstop))
dat2 = get_data(2)
dat2.x = dat2.x - tstart
dat1.staterror = staterror['1pin1at'] * np.ones_like(dat2.x) # Set up pseudo statistical error 

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

# mymethod = NelderMead()
mymethod = LevMar()
mymodel = get_model()
mystat = DeadChi()

fitobj = Fit( dat1, mymodel, mystat, mymethod )

def fitall():
    for detector in ('acis', 'hrcs', 'hrci'):
        for pitch in ('50', '90', '150'):
            thaw(getattr(dea, detector + pitch))
        print 'Fitting', detector, 'settling temps at', time.ctime()
        fit(1,2)
        #fitres = fitobj.fit(1,2)
        #print fitres
        freeze(dea)
        print 'Done at', time.ctime()

    thaw(dea.u01)
    thaw(dea.u12)
    thaw(dea.c1)
    thaw(dea.c2)
    thaw(dea.u01quad)
    print 'Fitting time const params at', time.ctime()
    fit(1,2)
    # fitres = fitobj.fit(1,2)
    # print fitres
    freeze(dea)
    print 'Done at', time.ctime()

    plot_fit_resid()

    print dea
