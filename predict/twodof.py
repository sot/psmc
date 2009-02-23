"""
******   2mass.py   *******

Define constants and a TwoMass class that calculates the predicted temperature
using this model.
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
pardefault = dict(acis150 =    27.1999,
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

    @param state: state vector (with power, pitch, simpos)
    @param par: model parameter values
    @param t: numpy array of input times (sec)
    @param Ti: Vector of initial temperatures (1pin1at and 1pdeaat)

    @return: numpy array of temperatures at times C{t}
    """

    # Calculate as for the following, but in a vectorized form:
##       exp_l1_t = math.exp(l1*t)
##       exp_l2_t = math.exp(l2*t)
##       T1 = np.matrix([[(exp_l1_t-1)/l1, 0 ],
##                       [0, (exp_l2_t-1)/l2]]) * self.eigvecinvs * self.heat
##       T2 = np.matrix([[exp_l1_t, 0  ],
##                       [0,  exp_l2_t]]) * self.eigvecinvs * self.Ti
##       return self.eigvecs * (T1 + T2)

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

        @param states: numpy recarray of states (must be contiguous)
        @param pin0: initial value (degC) of 1pin1at at states[0]['tstart']
        @param dea0: initial value (degC) of 1pdeaat at states[0]['tstart']
        @param dt: approximate time spacing for calculating model values (secs)

        @return: TwoDOF object
        """
        self.states = states
        self.T_pin0 = T_pin0
        self.T_dea0 = T_dea0
        self.dt = dt
        self.par = None

    def interpolate_msid_temp(self, msid, t):
        out = self.predT[0,:] if msid == '1pin1at' else self.predT[1,:]
        return Ska.Numpy.interpolate(out + KtoC, self.tval, t)

    def calc_model(self, t, par=pardefault, msid='1pdeaat'):
        """
        @param t: array of times at which to return the model temperatures
        @param par: model parameters
        @param msid: desired MSID ('1pin1at' or '1pdeaat')

        @return: array of temperatures for C{msid}
        """
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
