import numpy as np
import twodof
import characteristics as char

simz_hrcs = -99616
power = dict((x[0:3], x[3]) for x in char.psmc_power)
cols = 'tstart  tstop  power  pitch  simpos'.split()

pitchs = range(45, 170, 1)
settle_temps = []

for pitch in pitchs:
    states = []
    states.append((0., 500000., power[0, 1, 0], pitch, simz_hrcs))

    states = np.rec.fromrecords(states, names=cols)

    dea0 = 25.
    pin0 = 35.
    times = np.arange(states['tstart'][0], states['tstop'][-1], 10000.)

    T_pin, T_dea = twodof.calc_twodof_model(states, pin0, dea0, times,
                                            par=char.model_par, dt=10000.)
    settle_temps.append(T_dea[-1])
                  
figure(1, figsize=(6, 4.5))
clf()
plot(pitchs, settle_temps)
ylim(0, 15)
ylabel('1PDEAAT (degC)')
xlabel('Pitch (degrees)')
title('Final temp at HRC-S (FEP=0, clock=0, vid=1)')
savefig('scs107_settling.png')       
