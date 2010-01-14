#!/usr/bin/env python

# Hack to print out text to be inserted into characteristics_Thermal.m


import os
import sys

# get the characteristics
SKA = os.environ['SKA']
char_dir = os.path.join( SKA, 'share', 'psmc')
sys.path.insert(-1,char_dir)

import characteristics

print """

%%%%%% Begin Generated Text from SOT Python PSMC Characteristics %%%%%%

%% SOT VERSION %s

""" % characteristics.VERSION

# all the stuff that doesn't change in the python characteristics
print """
%1PIN1AT thermal model parameters

Thermal.msid_1pdeaat.msid = '1PDEAAT';
Thermal.msid_1pdeaat.units = 'Deg C';

%1PIN1AT model default initial temperature
Thermal.msid_1pin1at.default_initial_temperature = 35;
Thermal.msid_1pdeaat.default_initial_temperature = 40;                          

% separation in seconds of samples returned by model calculation within each
% state
Thermal.msid_1pdeaat.instate_calc_sample_sep = 32.8;

% separation in seconds of samples returned by main psmc model calculation
Thermal.msid_1pdeaat.sample_sep = 32.8;

% preferred sampling of pitch for pitch state creation                                             
Thermal.msid_1pdeaat.model_pitch_sampling = 30; % every 30th 10s sample     

"""

# the stuff that can
model_pars = characteristics.model_par.keys()
model_pars.sort()
model_string = ''
for par in model_pars:
    new_string = "'%s' ,  %6.2f " % ( par, characteristics.model_par[par])
    if model_string == '':
        model_string += new_string
    else:
        model_string += ", ... \n %s" % new_string 

print "Thermal.msid_1pdeaat.model_defaults = struct( %s ); \n" % model_string


print "%PSMC average power for each state (fep_count, vid_board, clocking)"
print "% note that calcThermal1PDEAAT.m does not allow for clocking = 1 and vidboard = 0"
print "% so those combinations from python characteristics are excluded"
print "%['pk_ fep_count _ vid_board _ clocking', power_avg in watts]"


# the python structure is a tuple of tuples, so this is trickier
# a string key is made over fep_count, vid_board, clocking and the last value is the power
power_string = ''
for power_comb in characteristics.psmc_power:
    # skip clocking on, vidboard off ones
    if ( power_comb[1] == 0 and power_comb[2] == 1):
        pass
    else:
        power_key = "pk_%d_%d_%d" % (power_comb[0:3])
        new_string = "'%s', %6.2f " % ( power_key, power_comb[3] )
        if power_string == '':
            power_string += new_string
        else:
            power_string += ", ... \n %s" % new_string
        

print "Thermal.msid_1pdeaat.psmc_power = struct( %s ); \n" % power_string



print """
% Old 1PIN1AT yellow, red, & reference limits (reference draws a green line -"
% -10000 for ref means don't plot the line)"
Thermal.msid_1pin1at.yellow_limit    = 41;
Thermal.msid_1pin1at.red_limit       = 46;
Thermal.msid_1pin1at.reference_limit = 38.5;
"""

print "% ACIS PSMC hardware yellow/red limits"
print ("Thermal.msid_1pdeaat.T_dea_yellow = %6.2f ; %% 1PDEAAT yellow limit (degC)"  
       % characteristics.T_dea_yellow )
print ("Thermal.msid_1pdeaat.T_dea_red = %6.2f; %% 1PDEAAT red limit (degC)"  
       % characteristics.T_dea_red )
print ("Thermal.msid_1pin1at.T_pin_yellow = %6.2f ; %% 1PIN1AT yellow limit (degC) " 
       % characteristics.T_pin_yellow )
print ("Thermal.msid_1pin1at.T_pin_red = %6.2f ; %% 1PIN1AT red limit (degC)  " 
       % characteristics.T_pin_red )

print "% Mission planning margin from yellow limit reflecting accepted level of"
print "% uncertainty (1%) in PSMC model predictions."
print "Thermal.msid_1pdeaat.T_dea_margin = %5.2f; " % characteristics.T_dea_margin
print "Thermal.msid_1pin1at.T_pin_margin = %5.2f; " % characteristics.T_pin_margin

print """

%%%%%% End Generated Text from SOT Python PSMC Characteristics %%%%%%
"""
