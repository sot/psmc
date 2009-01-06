import sys

if 'site-packages' not in sys.path:
    sys.path.append('site-packages')
import pkg_resources
pkg_resources.require('Chandra.Time', 'Ska.Table')

import Chandra.Time
import numpy as np
import twodof
import Ska.Table

parnames = sorted(twodof.pardefault)
def psmc_temps(msid):
    """Evaluate PSMC temperatures at given times."""
    def psmc_temp(pars, t):
        return twomass.calc_temp(t, msid=msid, par=dict(zip(parnames, pars)))
    return psmc_temp

if 'states08' not in globals():
    print 'Reading states08'
    states08 = Ska.Table.read_fits_table('2008_intervals.fits')

# Train period
date0 = Chandra.Time.DateTime('2008-04-09T00:00:00')
date1 = Chandra.Time.DateTime('2008-12-28T00:00:00')
#date0 = Chandra.Time.DateTime('2008-06-01T00:00:00')
#date1 = Chandra.Time.DateTime('2008-09-01T00:00:00')
states = states08[ (states08['tstart'] > date0.secs) & (states08['tstop'] < date1.secs) ]
tstart = states[0].tstart
tstop = states[-1].tstop
states['tstart'] -= tstart
states['tstop'] -= tstart

if 'tlm08' not in globals():
     tlm08 = Ska.Table.read_fits_table('telem_08.fits')
tlm = tlm08[ (tlm08['date'] > tstart) & (tlm08['date'] < tstop) ]

print "loading pdeaat"
load_data(1, 'telem_08.fits[cols date, 1pdeaat][date>%f][date<%f]' % (tstart, tstop))
dat1 = get_data(1)
dat1.x = dat1.x - tstart
dat1.staterror = 1.25 * np.ones_like(dat1.x)

print "loading pin1at"
load_data(2, 'telem_08.fits[cols date, 1pin1at][date>%f][date<%f]' % (tstart, tstart+300))
dat2 = get_data(2)
dat2.x = dat2.x - tstart
dat2.staterror = 1.0 * np.ones_like(dat2.x)

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

for parname in parnames:
    setattr(dea, parname, twodof.pardefault[parname])

freeze(dea)

def fitall():
    for detector in ('acis', 'hrcs', 'hrci'):
        for pitch in ('50', '90', '150'):
            thaw(getattr(dea, detector + pitch))
        print 'Fitting', detector, 'settling temps at', time.ctime()
        fit()
        freeze(dea)
        print 'Done at', time.ctime()

    thaw(dea.u01)
    thaw(dea.u12)
    thaw(dea.c1)
    thaw(dea.c2)
    thaw(dea.u01quad)
    print 'Fitting time const params at', time.ctime
    fit()
    freeze(dea)
    print 'Done at', time.ctime

    plot_fit_resid()

    print dea
