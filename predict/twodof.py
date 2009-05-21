"""
Calculate ACIS PSMC temperatures using a two degree-of-freedom model.
"""

import numpy as np
import math

import pkg_resources
pkg_resources.require('Ska.Numpy')
import Ska.Numpy

# Define a number of module constants that are tuned.

CtoK = 273.15
KtoC = -CtoK

# Based on chi2gehrels fit of both 1pdeaat and 1pin1at
# over the range 2008-04-09 - 2008-12-28
_pardefault = dict(acis150 =    27.1999,
                  acis50  =    55.4133,
                  acis90  =    31.2034,
                  c1      =    122.204,
                  c2      =    16.5221,
                  hrci150 =    33.2693,
                  hrci50  =    43.8671,
                  hrci90  =    29.8505,
                  hrcs150 =     38.385,
                  hrcs50  =    33.1306,
                  hrcs90  =    32.2106,
                  u01     =    6.23487,
                  u01quad =  -0.524545,
                  u12     =    7.76193)

# Based on levmar fit of both 1pdeaat and 1pin1at
# over the range 2009-01-01 - 2009-04-01
pardefault = dict(acis150  =      29.0302,
                  acis50   =      56.0669,
                  acis90   =      29.7084,
                  c1       =      93.5736,
                  c2       =      12.9992,
                  hrci150  =      41.3023,
                  hrci50   =      40.5857,
                  hrci90   =      30.6498,
                  hrcs150  =      39.9622,
                  hrcs50   =      33.4304,
                  hrcs90   =      33.2913,
                  u01      =      5.64142,
                  u01quad  =     -1.09691,
                  u12      =      8.29004)

# From levmar fits of only 1pdeaat over 2009-01-03 - 2009-04-03
_pardefault = dict(acis150  =  28.0263,     
                  acis50   =  54.036 ,     
                  acis90   =  28.1335,     
                  c1       =  182.457,     
                  c2       =  27.6601,     
                  hrci150  =  31.9251,     
                  hrci50   =  41.7947,     
                  hrci90   =  17.7964,     
                  hrcs150  =  38.0591,     
                  hrcs50   =  32.588 ,     
                  hrcs90   =  33.0679,     
                  u01      =  12.477 ,     
                  u01quad  =  -0.0935,
                  u12      =  5.7223      )

def Tf_zero_power(par, pitch, simz):
    """Settling temperature (Tf) at zero PSMC power.
    The corresponds to the T0 parameter of the two-mass model.
    """
    U01 = par['u01'] + par['u01quad'] * ((pitch-110)/60)**2
    U12 = par['u12']

    if simz < -85000:          # HRC-S
        det = 'hrcs'
    elif simz < 0:
        det = 'hrci'
    else:
        det = 'acis'
        
    pitchs = np.array([50., 90., 150.])
    tfzps = np.array([par[det + '50'],
                      par[det + '90'],
                      par[det + '150']], dtype='float32')

    # Zero power temp T0 = T2 - Pp(1/U01 + 1/U12)
    Pp = 128                    # For 6 chips => Pp = 128
    T2 = Ska.Numpy.interpolate(tfzps, pitchs, [pitch])[0]

    return T2 - Pp * (1./U01 + 1./U12) + CtoK

def calc_state_temps(state, par, t, Ti, eigvals, eigvecs, eigvecinvs, U01, C1, C2):
    """Calculate predicted temperatures at the input times for a given state
    using the two-mass model.

    Evaluate the following but do so in a vectorized form::

      exp_l1_t = math.exp(l1*t)
      exp_l2_t = math.exp(l2*t)
      T1 = np.matrix([[(exp_l1_t-1)/l1, 0 ],
                      [0, (exp_l2_t-1)/l2]]) * self.eigvecinvs * self.heat
      T2 = np.matrix([[exp_l1_t, 0  ],
                      [0,  exp_l2_t]]) * self.eigvecinvs * self.Ti
      return self.eigvecs * (T1 + T2)

    :param state: state vector (with power, pitch, simpos)
    :param par: model parameter values
    :param t: numpy array of input times (sec)
    :param Ti: Vector of initial temperatures (1pin1at and 1pdeaat)

    :rtype: numpy array of temperatures at times C{t}
    """
    # Model settling temperature at zero power for given pitch and sim-z
    Tf_zp = Tf_zero_power(par, state['pitch'], state['simpos'])
    
    heat = np.array([[U01 * (Tf_zp / C1)],
                     [state['power'] / C2]])
    l1 = eigvals[0]
    l2 = eigvals[1]
    Ti = Ti

    # print 'pitch=%f tau1=%.2f tau2=%.2f' % (state['pitch'], 1./l1, 1./l2)

    t_ksec = t / 1000.
    exp_l1_t = np.exp(l1*t_ksec)
    exp_l2_t = np.exp(l2*t_ksec)

    lenM = len(t) * 2 * 2
    M1 = np.zeros(lenM)
    M1[0:lenM:4] = (exp_l1_t-1)/l1
    M1[3:lenM:4] = (exp_l2_t-1)/l2
    M1 = M1.reshape(len(t), 2, 2)
    T1 = np.dot(np.dot(M1, eigvecinvs), heat)

    M2 = np.zeros(lenM)
    M2[0:lenM:4] = exp_l1_t
    M2[3:lenM:4] = exp_l2_t
    M2 = M2.reshape(len(t), 2, 2)
    T2 = np.dot(np.dot(M2, eigvecinvs), Ti)

    return np.dot(eigvecs, (T1 + T2)).reshape(2, -1)

class TwoDOF(object):
    def __init__(self, states, T_pin0, T_dea0, dt=32.8):
        """Initialize model object to predict the PSMC temperatures 1PDEAAT and
        1PIN1AT given the list of configuration C{states} and initial
        temperatures C{dea_T0} and C{pin_T0}.

        The states recarray must include the following columns::
          tstart  tstop  power  pitch  simpos

        :param states: numpy recarray of states (must be contiguous)
        :param pin0: initial value (degC) of 1pin1at at states[0]['tstart']
        :param dea0: initial value (degC) of 1pdeaat at states[0]['tstart']
        :param dt: approximate time spacing for calculating model values (secs)

        :rtype: TwoDOF object
        """
        self.states = states
        self.T_pin0 = T_pin0
        self.T_dea0 = T_dea0
        self.dt = dt
        self.par = None

    def interpolate_msid_temp(self, msid, t):
        """Return predicted temperatures in degC for ``msid`` at times ``t``."""
        out = self.predT[0,:] if msid == '1pin1at' else self.predT[1,:]
        return Ska.Numpy.interpolate(out + KtoC, self.tval, t)

    def calc_model(self, t, par=None, msid='1pdeaat'):
        """
        :param t: array of times at which to return the model temperatures
        :param par: model parameters
        :param msid: desired MSID ('1pin1at' or '1pdeaat')

        :rtype: array of temperatures for C{msid}
        """
        if par is None:
            par = pardefault

        # If params are unchanged then use existing values
        if par == self.par:
            return self.interpolate_msid_temp(msid, t)

        predT = None
        predTs = []
        tvals = []
        Ti = np.array([[self.T_pin0],
                       [self.T_dea0]]) + CtoK

        for state in self.states:
            U01 = par['u01'] + par['u01quad'] * ((state['pitch']-110)/60)**2
            U12 = par['u12']
            C1 = par['c1']
            C2 = par['c2']

            M = np.array([[-(U01 + U12) / C1 ,  U12 / C1],
                          [U12 / C2          , -U12 / C2]])
            eigvals, eigvecs = np.linalg.eig(M)
            eigvecinvs = np.linalg.inv(eigvecs)

            t0 = state['tstart']

            # Make array of times. 
            n_t = int((state['tstop'] - state['tstart']) / self.dt)
            tval = np.linspace(state['tstart'], state['tstop'], n_t+2)

            # Calculated predicted temperatures for this state
            predT = calc_state_temps(state, par, tval - t0, Ti,
                                     eigvals, eigvecs, eigvecinvs,
                                     U01, C1, C2)
            tvals.append(tval)
            predTs.append(predT)

            Ti = predT[:, -1].reshape(2,1)

        self.tval = np.hstack(tvals)
        self.predT = np.hstack(predTs)
        self.par = par
        
        return self.interpolate_msid_temp(msid, t)

def calc_twodof_model(states, T_pin0, T_dea0, times, dt=32.8, par=None):
    """Calculate the PSMC temperatures 1PDEAAT and 1PIN1AT given the list of
    configuration ``states`` and initial temperatures ``dea_T0`` and ``pin_T0``.

    The ``states`` input must be an iterable list with the following keys::
      tstart  tstop  power  pitch  simpos

    :param states: iterable list of states (must be contiguous)
    :param T_pin0: initial value (degC) of 1pin1at at states[0]['tstart']
    :param T_dea0: initial value (degC) of 1pdeaat at states[0]['tstart']
    :param times: array of times at which to return the model temperatures
    :param dt: approximate time spacing for calculating model values (secs)
    :param par: model parameters dictionary

    :rtype: predicted temperature arrays (T_pin, T_dea)
    """
    if par is None:
        par = pardefault         # Model parameters from "characteristics"

    predTs = []
    tvals = []
    Ti = np.array([[T_pin0],
                   [T_dea0]]) + CtoK

    for state in states:
        U01 = par['u01'] + par['u01quad'] * ((state['pitch']-110)/60)**2
        U12 = par['u12']
        C1 = par['c1']
        C2 = par['c2']

        M = np.array([[-(U01 + U12) / C1 ,  U12 / C1],
                      [U12 / C2          , -U12 / C2]])
        eigvals, eigvecs = np.linalg.eig(M)
        eigvecinvs = np.linalg.inv(eigvecs)

        t0 = state['tstart']

        # Make array of times. 
        n_t = int((state['tstop'] - state['tstart']) / dt)
        tval = np.linspace(state['tstart'], state['tstop'], n_t+2)

        # Calculated predicted temperatures for this state
        predT = calc_state_temps(state, par, tval - t0, Ti,
                                 eigvals, eigvecs, eigvecinvs,
                                 U01, C1, C2)
        tvals.append(tval)
        predTs.append(predT)

        Ti = predT[:, -1].reshape(2,1)

    tval = np.hstack(tvals)
    predT = np.hstack(predTs)

    # Interpolate predicted temperatures in degC at desired output times
    T_pin = Ska.Numpy.interpolate(predT[0,:] + KtoC, tval, times)
    T_dea = Ska.Numpy.interpolate(predT[1,:] + KtoC, tval, times)

    return T_pin, T_dea
