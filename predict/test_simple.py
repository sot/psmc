import numpy as np
import predict

cols = 'tstart  tstop  power  pitch  simpos'.split()
states = [(    0., 10000., 100., 60.,  75766.),
          (10000., 120000.,  60., 140., 75766.)]
states = np.rec.fromrecords(states, names=cols)

dea0 = 45.
pin0 = 35.
predstates = predict.predict(states, pin0, dea0)


