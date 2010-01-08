#!/usr/bin/env python
import Ska.Table
from Ska.TelemArchive.fetch import fetch
from Chandra.Time import DateTime
import numpy as np
from Ska.DBI import DBI
import re
import characteristics
from pylab import *
from Ska.Matplotlib import plot_cxctime, pointpair
import twodof

def main():
    mstate_file = 'states.txt'
    mtemp_file = '1pdeaat.txt'    
    mstates = Ska.Table.read_ascii_table(mstate_file)
    marray = []
    for state in mstates:
        state_list = list( state )
        state_list.append(DateTime(state['tstart']).secs)
        state_list.append(DateTime(state['tstop']).secs)
        marray.append(state_list)

    matlab_states = np.core.records.fromrecords( marray, names ='datestart,datestop,obsid,simpos,ccd_count,fep_count,vid_board,clocking,power,pitch,tstart,tstop')
    matlab_pred = Ska.Table.read_ascii_table( mtemp_file )

    dates = matlab_pred['Time']
    state0 = matlab_states[0]
    msid_string = { '1pdeaat' : '1PDEAAT Prediction (degC)',
                    '1pin1at' : '1PIN1AT Prediction' }
    dea0 = matlab_pred[0][msid_string['1pdeaat']]
    pin0 = matlab_pred[0][msid_string['1pin1at']]
    times = DateTime( dates ).secs

    ( T_pin, T_dea ) = twodof.calc_twodof_model( matlab_states, pin0, dea0, times, characteristics.model_par)
    preds = np.core.records.fromarrays([ times, T_pin, T_dea], names='time,1pin1at,1pdeaat')

    pyt_file = open('python_temps.csv', 'w')

    pyt_file.write("Time\t%s\t%s\n" % ( msid_string['1pdeaat'], msid_string['1pin1at'] ))
    for pred in preds:
        pyt_file.write("%s\t%s\t%s\n" % ( DateTime(pred['time']).date, pred['1pdeaat'], pred['1pin1at']))

    for msid in ('1pdeaat', '1pin1at'):
        figure(1,figsize=(5,3.75))
        plot_cxctime( times, matlab_pred[msid_string[msid]], fmt='r.')
        plot_cxctime( times, preds[msid], fmt='b.')
        xlabel('CXC Time')
        ylabel('%s (Deg C)' % msid )
        savefig('%s.png' % msid )
        clf()
        hist( matlab_pred[msid_string[msid]] - preds[msid], bins=20)
        xlabel('Diff (Deg C)')
        title("matlab - python")
        savefig('%s_hist.png' % msid )
        clf()
    
if __name__ == "__main__":          
    main()
