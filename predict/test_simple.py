import numpy as np
import predict
import twodof

cols = 'tstart  tstop  power  pitch  simpos'.split()
states = []
for i in range(3):
    states.append((i*10000., (i+1)*10000., 60., 100.-i*20, 75766.))
    
states = np.rec.fromrecords(states, names=cols)

dea0 = 45.
pin0 = 35.
pred = predict.predict(states, pin0, dea0, dt=32.8,
                       tstartcol='tstart', tstopcol='tstop')

twomass = twodof.TwoDOF(states, pin0, dea0)
times = np.arange(states['tstart'][0], states['tstop'][-1], 32.8)
T_dea = twomass.calc_temp(times)
