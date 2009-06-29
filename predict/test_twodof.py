import numpy as np
import twodof
import Ska.Table
import time
import Chandra.Time
import sys

if 'tlm08' not in globals():
    tlm08 = Ska.Table.read_fits_table('telem_08.fits')

if 'states08' not in globals():
    states08 = Ska.Table.read_fits_table('2008_intervals.fits')

date0 = Chandra.Time.DateTime('2008-06-01T00:00:00')
date1 = Chandra.Time.DateTime('2008-12-01T00:00:00')

states = states08[ (states08['tstart'] > date0.secs) & (states08['tstop'] < date1.secs) ]
tstart = states[0].tstart
tstop = states[-1].tstop

tlm = tlm08[ (tlm08['date'] > tstart) & (tlm08['date'] < tstop) ]

dea0 = tlm[0]['1pdeaat']
pin0 = tlm[0]['1pin1at']
twomass = twodof.TwoDOF(states, pin0, dea0)
times = tlm['date']

clock0 = time.clock()
# T_dea = twomass.calc_model(times)
T_pin, T_dea = twodof.calc_twodof_model(states, pin0, dea0, times)
print 'Execution time:', time.clock() - clock0

hot = tlm['1pdeaat'] > 40

figure(1)
clf()
plot((times-tstart)/1000., tlm['1pdeaat'])
plot((times-tstart)/1000., T_dea)

figure(2, figsize=(6,4.5))
clf()
resid = tlm['1pdeaat'] - T_dea
hist(resid, bins=50, label='All')
title('1pdeaat: Actual - Model')
xlabel('Model error (degC)')
ylabel('Samples')

resid = tlm['1pdeaat'] - T_dea
hist(resid[hot], bins=50, label='1pdeaat > 40')
title('1pdeaat: Actual - Model')
xlabel('Model error (degC)')
ylabel('Samples')
#savefig('fit_resid_hist.png')

figure(3, figsize=(6,4.5))
clf()
hist(resid, bins=50, log=True)
title('1pdeaat: Actual - Model')
xlabel('Model error (degC)')
ylabel('Samples')
#savefig('fit_resid_hist_log.png')


print 'Stddev (all):', std(resid)

print 'Stddev (T>40):', std(resid[hot])

sortresid = sorted(resid)
l = len(resid)
print 'Quantiles:'
print '1%%: %.2f' % sortresid[int(l*0.01)]
print '5%%: %.2f' % sortresid[int(l*0.05)]
print '16%%: %.2f' % sortresid[int(l*0.16)]
print '50%%: %.2f' % sortresid[int(l*0.50)]
print '84%%: %.2f' % sortresid[int(l*0.84)]
print '95%%: %.2f' % sortresid[int(l*0.95)]
print '99%%: %.2f' % sortresid[int(l*0.99)]

