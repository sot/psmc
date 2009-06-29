import Chandra.Time
import Ska.Numpy
import Ska.Table
import Ska.DBI
import predict

def pointpair(x, y=None):
    if y is None:
        y = x
    return np.array([x, y]).reshape(-1, order='F')

if 'd08' not in globals():
    d08 = Ska.Table.read_fits_table('telem_08.fits')

if 'db' not in globals():
    db = Ska.DBI.DBI(dbi='sqlite',server='obsid_check.db', numpy=True)

date0 = '2008-03-08T12:00:00'
date1 = '2008-04-07T00:00:00'
date0 = '2008-05-01T00:00:00'
date1 = '2008-05-07T01:00:00'
t0 = Chandra.Time.DateTime(date0).secs
t1 = Chandra.Time.DateTime(date1).secs

cpi = db.fetchall("""select * from waninfo
                     where tstop > %f
                     and tstart < %f
                     and tstop - tstart > 32.8
                     order by tstart""" % (t0, t1))

d = d08[ (d08['date'] > t0) & (d08['date'] < t1) ]
d['date'] -= t0

pwr = (d['1de28avo'] * d['1deicacu'] +
       d['1dp28avo'] * d['1dpicacu'] +
       d['1dp28bvo'] * d['1dpicbcu'])
pwr_smooth = Ska.Numpy.smooth(pwr, 20)

times = np.array([cpi['tstart'], cpi['tstop']]).reshape(-1, order='F') - t0
times = append(times, times[-1]+40)
ok = np.abs(times[1:] - times[:-1]) > 0.01
times = times[ok]

itimes = searchsorted(d['date'], times)
pwr_avg = np.array([pwr[ itimes[i]:itimes[i+1] ].mean() for i in range(len(itimes)-1)])
pwr_tstart = times[:-1]
pwr_tstop = times[1:]

# plot(pointpair(pwr_tstart, pwr_tstop), pointpair(pwr_avg))
# plot(d['date'], pwr_smooth)

pwr_avg_sampled = pwr_avg[ searchsorted(pwr_tstop, d['date'])]

dnew = np.rec.fromarrays([d['date'], d['tscpos'], d['point_suncentang'], pwr_avg_sampled],
                         names=['time', 'simpos', 'pitch', 'power'])

dcom = Ska.Numpy.compress(dnew, delta=dict(tscpos=3, pitch=3.0, power=10.0), indexcol='time')

t = pointpair(dcom['time_start'], dcom['time_stop'])/1000.

tlm_t = dnew['time']/1000.
tlm_power = pwr_smooth
tlm_simpos = dnew['simpos']
tlm_pitch = dnew['pitch']

clf()
subplot(4,1,1)
plot(t, pointpair(dcom['power']))
plot(tlm_t,pwr_smooth)
ylabel('Power (watts)')
title(date0 + ' to ' + date1)

subplot(4,1,2)
plot(t, pointpair(dcom['pitch']))
ylabel('Pitch (deg)')
plot(tlm_t, dnew['pitch'])

subplot(4,1,3)
plot(t, pointpair(dcom['simpos']))
plot(tlm_t, dnew['simpos'])
ylabel('SIM pos (steps)')

# Ska.Table.write_fits_table('tlm_states.fits', dcom)
pred = predict.predict(dcom, pin0=d[0]['1pin1at'], dea0=d[0]['1pdeaat'])

subplot(4,1,4)
plot(d['date']/1000., d['1pdeaat'])
plot(pred['time']/1000., pred['1pdeaat'])
ylabel('1pdeaat (degC)')
xlabel('Time (ksecs)')
