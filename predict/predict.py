import numpy as np
import twomass
from twomass import DegCtoDegK as CtoK, DegKtoDegC as KtoC

def state_diff(c1, c2):
    if c2 is None:
        return True
    else:
        return (abs(c1['pitch'] - c2['pitch']) > 1
                or abs(c1['simpos'] - c2['simpos']) > 2
                or abs(c1['power'] - c2['power']) > 3
                )

def Pp(nccd):
    """
    1 56.8689271154 2.11593544576
    2 71.6391037092 1.80554630974
    3 nan 0.0
    4 99.6076450722 1.67294461105
    5 112.932698413 2.1489397187
    6 128.136824396 2.26711801838
    (y1-y0)*(x-x0)/(x1-x0) + y0
    """
    return (128.1-56.9) * (nccd - 1) / (6-1) + 56.9

def predict(states, pin0, dea0, dt=32.8):
    """Predict the PSMC temperatures 1pdeaat and 1pin1at given the list of
    configuration C{states} and initial temperatures C{dea_T0} and C{pin_T0}.

    The states recarray must include the following columns::
      tstart  tstop  power  pitch  simpos

    @param states: numpy recarray of states (must be contiguous)
    @param pin0: initial value (degC) of 1pin1at at states[0]['tstart']
    @param dea0: initial value (degC) of 1pdeaat at states[0]['tstart']
    @param dt: approximate time spacing of output values (secs)

    @return: recarray with cols time, 1pin1at, 1pdeaat, power, pitch, and simpos
    """
    
    predT = None
    predstates = []

    for state in states:
        t0 = state['tstart']
        T0 = twomass.Ext_T0(state['pitch'], state['simpos'])
        if predT is None:
            Ti = np.matrix([[pin0],
                            [dea0]]) + CtoK
        else:
            Ti = predT

        model = twomass.TwoMass(state['power'], T0, Ti)

        n_ts = int((state['tstop'] - state['tstart']) / dt)
        for t in np.linspace(state['tstart'], state['tstop'], n_ts):
            predT = model.calcT(t - t0)
            predstates.append((t, predT[0,0].tolist() + KtoC, predT[1,0].tolist() + KtoC,
                              state['power'], state['pitch'], state['simpos']))

    return np.rec.fromrecords(predstates,
                              formats=['f8', 'f4', 'f4', 'f4', 'f4', 'f4'],
                              names=['time', '1pin1at', '1pdeaat', 'power', 'pitch', 'simpos'])

