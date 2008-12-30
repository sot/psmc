import ParseTable
import numpy as np
from glob import glob
import twomass
from twomass import DegCtoDegK as CtoK, DegKtoDegC as KtoC
import smooth
import math
import Interpolate
import sys

if 'cmdstates' not in globals():
    for cmdfile in glob('jan2108b/CL*.fits'):
        print 'Reading', cmdfile
        data = ParseTable.parse_fits_table(cmdfile)
        try:
            cmdstates = np.append(cmdstates, data)
        except NameError:
            cmdstates = data

    time0 = cmdstates[0]['time']
    cmdstates['time'] = (cmdstates['time'] - time0) / 1000.
    ctime = cmdstates['time']

if 'telem' not in globals():
    telem = ParseTable.parse_ascii_table('jan2108b/telem.dat')
    telem['date'] = (telem['date'] - time0) / 1000.
    pwrdea = telem['1de28avo'] * telem['1deicacu']
    pwrdpaa = telem['1dp28avo'] * telem['1dpicacu']
    pwrdpab = telem['1dp28bvo'] * telem['1dpicbcu']
    pwr = smooth.smooth(pwrdea + pwrdpaa + pwrdpab, window_len=33, window='flat')
    ttime = telem['date']

if 'cpwr' not in globals():
    # Add pwr column to cmdstates.  There must be a better way...
    cpwr = Interpolate.interp(pwr, ttime, ctime)
    cmdstates_list = [cmdstate + (cpwr[i],) for i, cmdstate in enumerate(cmdstates.tolist())]
    cmdstates = np.rec.array(cmdstates_list, dtype=np.dtype(cmdstates.dtype.descr + [('power', '>f8')]))

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

cmdstate0 = None
T = np.matrix([[],
               []])
nextT = None
predstate = []

print 'Start prediction ...'
for cmdstate in cmdstates[0:-1:1]:
    if state_diff(cmdstate, cmdstate0):
        cmdstate0 = cmdstate
        t0 = cmdstate0['time']
        T0 = twomass.Ext_T0(cmdstate0['pitch'], cmdstate0['simpos'])
        if nextT is None:
            Ti = np.matrix([[telem[0]['1pin1at']],
                            [telem[0]['1pdeaat']]]) + CtoK
        else:
            Ti = nextT
        Pp0 = cmdstate0['power']
        Pp_from_nccd = Pp(cmdstate0['n_ccds_on'])
        model = twomass.TwoMass(Pp0, T0, Ti)

    t = cmdstate['time']
    nextT = model.calcT(t - t0)
    predstate.append((t,
                      Pp0, Pp_from_nccd,
                      nextT[0,0].tolist(), nextT[1,0].tolist(),
                      cmdstate0['pitch'], cmdstate0['simpos']))
    T = np.append(T, nextT, 1)

print 'Finish'

sys.exit(0)

T = np.array(T)
cpin = T[0,:].flatten() + KtoC
cdea = T[1,:].flatten() + KtoC
tpin = telem['1pin1at']
tdea = telem['1pdeaat']
predstate = np.rec.array(predstate, names=('time', 'power', 'power_from_nccd',
                                              '1pin1at', '1pdeaat',
                                              'pitch', 'tscpos'))
if 1:
    figure(1)
    clf()
    ctime = predstate['time']
    subplot(2,1,1)
    plot(ctime, cdea)
    plot(ttime, tdea)
    ylabel('degC')
    title('1PDEAAT for JAN2108B')
    subplot(2,1,2)
    plot(ctime, cpin)
    plot(ttime, tpin)
    ylabel('degC')
    xlabel('Time (ksec)')
    title('1PIN1AT')
    # savefig('./jan2108b/temps.png')

    figure(2)
    clf()
    plot(ttime, pwr, 'g', label='Actual')
    # plot(ctime, predstate['power'],'r', label='Model power')
    plot(ctime, predstate['power_from_nccd'],'r', label='Power from N_CCD')
    xlabel('Time (ksec)')
    ylabel('Power (W)')
    title('PSMC power for JAN2108B')
    legend(loc=3)
    savefig('./jan2108b/power.png')


    figure(0)
    clf()
    tdea_ctime = Interpolate.interp(tdea, ttime, ctime)
    hist(tdea_ctime - cdea, bins=30)
    xlabel('Actual - predicted 1PDEAAT (degC)')
    ylabel('Frequency')
    title('Prediction model residuals for 1PDEAAT')
    # savefig('./jan2108b/resid_hist.png')
