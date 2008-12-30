"""
******   2mass.py   *******

Define constants and a TwoMass class that calculates the predicted temperature
using this model.
"""

import numpy as np
import math

# Define a number of module constants that are tuned.

DegCtoDegK = 273.15
DegKtoDegC = -DegCtoDegK

# U01: Conductance between 1PIN1AT and SIM external (W K^-1)
# U01 = Pp(6 CCD)- Pp(1) / T1(6)-T1(1)
tweak01 = 2.5
U01 = (128.1 - 56.9) / 5.3 / tweak01

# U12: Conductance between 1PIN1AT and 1PDEAAT (W K^-1)
# Calibrated by looking at change (6 vs N CCD) for 1PIN1AT vs. 1PDEAAT
U12 = U01 / 0.65

# C1: Heat capacitance for 1PIN1AT (W K^-1 ksec^-1)
# tau_pin ~= C1 / U01 ( / 3 arbitrarily)
C1 = U01 * 20. / 2 * 1.5


# C2: Heat capacitance for 1PDEAAT (W K^-1 ksec^-1)
# Pure guess for value now based on estimated time constant for
# change when PSMC power changes due to N_CCD changing.
C2 = C1 / 10. * 1

M = np.matrix([[-(U01 + U12) / C1 ,  U12 / C1],
               [U12 / C2          , -U12 / C2]])
eigvals, eigvecs = np.linalg.eig(M)
M_eigvecs = np.matrix(eigvecs)
M_eigvecinvs = np.linalg.inv(eigvecs)

class Ext_T0(object):
    """External (SIM) temperature, depending on SIM-Z and pitch (and optionally
    on MET)"""

    @staticmethod
    def sun_illum_acis(pitch):
        """Calculate a sun illumination function that emulates the observed variation
        of settling temperature with pitch.  The output is normalized to a peak of 1.0"""
        pitchr = np.radians(pitch)

        # Illumination of the "vertical" surface of the SIM on which the PSMC is mounted.
        # (i.e. the surface facing +X).  Beyond pitch=90 the surface is not illuminated.
        if pitch > 90:
            illumX = 0
        else:
            illumX =  math.cos(pitchr)

        # Illumination of the "horizontal" surface (facing -Z). First make a shadow
        # function that is one for P<90 then decreases linearly to 0 at P=105.
        # This is shadowing due to the SIM top hat.
        p0 = 90.
        p1 = 105.
        shadow = (p1 - pitch) / (p1 - p0)
        if pitch < p0:
            shadow = 1
        elif pitch > p1:
            shadow = 0
        illumZ = math.sin(pitchr) * shadow

        return illumX, illumZ

    def __init__(self, pitch, simz, met=None):
        self.pitch = pitch
        self.simz = simz
        self.met = met

        # T0 = T2 - Pp(1/U01 + 1/U12)
        if self.simz > 0:               # ACIS, more-or-less
            illumX, illumZ = Ext_T0.sun_illum_acis(pitch)
            T2 = 20 * (illumX + 0.75 * illumZ) + 30
            Pp = 128                    # For 6 chips => Pp = 128
        else:                           # HRC
            T2 = 34
            Pp = 112                    # 5 chips

        self.degC = T2 - Pp * (1./U01 + 1./U12)

    def _get_degK(self):
        return self._degK

    def _set_degK(self, degK):
        self._degK = degK

    degK = property(_get_degK, _set_degK)
        
    def _get_degC(self):
        return self.degK + DegKtoDegC

    def _set_degC(self, degC):
        self.degK = degC + DegCtoDegK

    def __str__(self):
        return 'Ext_T0: <pitch=%.1f simz=%.0f degC=%.1f>' % (self.pitch, self.simz, self.degC)

    degC = property(_get_degC, _set_degC)
        
class TwoMass(object):
    def __init__(self, Pp, T0, Ti):
        self.heat = np.matrix([[U01 * T0.degK / C1],
                               [Pp / C2]])
        self.eigvecs = M_eigvecs
        self.eigvecinvs = M_eigvecinvs
        self.l1 = eigvals[0]
        self.l2 = eigvals[1]
        self.Ti = Ti

    def calcT(self, t):
        l1 = self.l1
        l2 = self.l2
        t_ksec = t / 1000.
        exp_l1_t = math.exp(l1*t_ksec)
        exp_l2_t = math.exp(l2*t_ksec)
        T1 = np.matrix([[(exp_l1_t-1)/l1,  0             ],
                        [0,               (exp_l2_t-1)/l2]]) * self.eigvecinvs * self.heat
        T2 = np.matrix([[exp_l1_t, 0       ],
                        [0,        exp_l2_t]]) * self.eigvecinvs * self.Ti
        # print 'twomass t=',t
        # print 'T1 =', self.eigvecs * T1
        # print 'T2 =', self.eigvecs * np.matrix([[exp_l1_t, 0],
        #                                        [0, exp_l2_t]]) * self.eigvecinvs
        return self.eigvecs * (T1 + T2)

