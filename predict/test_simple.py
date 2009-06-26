import numpy as np
import twodof
import characteristics as char

cols = 'tstart  tstop  power  pitch  simpos'.split()
states = []
states.append((    0., 10000.,  40., 150., -99162))
states.append((10000., 20000.,  80.,  90., -50360))
states.append((20000., 30000., 100., 130.,  75766))
states.append((30000., 40000., 120.,  55.,  93718))

states = np.rec.fromrecords(states, names=cols)

dea0 = 25.
pin0 = 35.
times = np.arange(states['tstart'][0], states['tstop'][-1], 32.8)

T_pin, T_dea = twodof.calc_twodof_model(states, pin0, dea0, times, par=char.model_par)
clf()
plot(times, T_pin, label='1pin1at')
plot(times, T_dea, label='1pdeaat')
legend()
