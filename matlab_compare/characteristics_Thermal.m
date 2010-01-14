function Thermal = characteristics_Thermal

%  characteristics_Thermal:     Parameters for thermal predictive models
%      used by MCC

%--------------------------------------
% Rev#    Date       Who      Purpose
% ----  --------  ---------------------
%  000  04/02/03  Tan Trinh   Original
%  001  10/14/03  Tan Trinh   Update equations for upcoming perihelion
%  002  07/01/04  Tan Trinh   Updated equations to matrix form (means bins
%                             can be of arbitrary size and begin and end
%                             points can be arbitrary; also updated settle
%                             temp calculator to accommodate
%  003  08/30/04  Tan Trinh   Added sine-exponent
%                             fitting for offsets, and removed settle temp
%                             calcs which will be done in drawPlot now.
%                             Also, updated new coeffs for TEPHIN
%  004  10/21/04  Tan Trinh   Added forw sun characteristics for TEPHIN
%  005  12/10/04  Tan Trinh   Added eclipse slope for TEPHIN
%  006  02/28/05  Tan Trinh   Added PLINE characteristics
%  007  03/24/05  Tan Trinh   Updated new coeffs for PM1THV1T & PM2THV1T
%                             Decreased TEPHIN reference limit from 97 to 96
%  008  04/11/05  Tan Trinh   Added time-thresholds for PLINE constraints
%                             Lowered 156-163 region for PLINES to 155-163
%  009  06/16/05  Tan Trinh   Added new gridded PLINE constraints
%  010  11/29/05  Tan Trinh   Updated new coefficients for TEPHIN; with
%                             previous model, telemetry ran hotter than
%                             predictions for hot attitudes
%  011  12/23/05  Tan Trinh   Updated TEPHIN yellow 105->115, ref 96->110
%                             Added TEPHIN benchmark temperatures for TEPHIN
%                             dwell time matrix
%  012  05/07/06  Tan Trinh   Added 1PIN1AT & 3TSCPOS characteristics
%  013  02/20/07  Tan Trinh   Updated TEPHIN coefficients and cosexp (for bias term)
%  014  06/05/07  S. Bucher   Updated reference limit to reflect MP Guideline change
%       06/13/07  Tan Trinh   Scheduled update TEPHIN coefficients and cosexp
%  015  06/18/07  Tan Trinh   Added characteristics for ACIS chips for 1PIN1AT model
%                             Changed TEPHIN dwell time limits to be notched
%                             to TEPHIN reference temperature
%  016  07/28/07  Tan Trinh   Updated TEPHIN coefficients & cosexp (actual cosexp change,
%                             not just for bias term) & limits
%  017  09/14/07  Tan Trinh   Edited pline constraint grid ... region 170-185 is now 152-185
%  018  12/11/07  Tan Trinh   Moved PLINE region lower bounds from 152-154, per PLINE 
%                             analysis, approved at FDB 12/06/07
%  019  04/23/08  Tan Trinh   Eliminated 154 base for PLINE region, approved
%                             at FDB 04/17/08  
%  020  07/14/08  S. Wilson   Added column to PLINE table to support dynamic
%                             PLINE regions in LIGER (tools updated to be 
%                             compatible).
%  021  04/07/09  M.Pendexter Updated TEPHIN yellow 119->133, ref 114->117
%                             Updated 1PIN1AT ref 36->38.5
%  022  10/05/09  J.Connelly  Added and updated PSMC model coefficients
%  023  12/03/09  M.Pendexter Updated TEPHIN ref limit 120->117
%  024  01/13/10  J.Connelly  Updated PSMC characteristics to SOT version 6
%-------------------------------------



%TEPHIN thermal model parameters
%TEPHIN model default initial temperature
Thermal.msid_tephin.default_initial_temperature = 80;

%TEPHIN yellow, red, & reference limits (reference draws a green line -
%-10000 for ref means don't plot the line)
Thermal.msid_tephin.yellow_limit    = 133;
Thermal.msid_tephin.red_limit       = 140;
Thermal.msid_tephin.reference_limit = 117;

%TEPHIN slope equations for each pitch range of the form  y = q1 * (x + q2) + q3
%NOTE: for the last bin (165-180), should repeat last equation so
%interpolation happens up to 170
Thermal.msid_tephin.slope_equation = [ 45  -0.12582  0.0 10.7447
50  -0.14974  0.0 14.0319
55  -0.11004  0.0 10.4501
60  -0.13593  0.0 14.6
65  -0.081734  0.0 9.5383
70  -0.073908  0.0 8.5127
75  -0.10927  0.0 13.0323
80  -0.10687  0.0 12.7027
85  -0.092475  0.0 11.6668
90  -0.10876  0.0 13.1454
95  -0.094978  0.0 11.9945
100  -0.12721  0.0 15.3679
105  -0.096958  0.0 12.3741
110  -0.12312  0.0 14.8493
115  -0.10524  0.0 13.0611
120  -0.13646  0.0 15.8481
125  -0.11783  0.0 13.5624
130  -0.10956  0.0 12.0965
135  -0.13666  0.0 14.1976
140  -0.13941  0.0 13.5326
145  -0.10599  0.0 9.3542
150  -0.095653  0.0 7.793
155  -0.095653  0.0 7.793 
160  -0.095653  0.0 7.793 
165  -0.11597  0.0 8.0091
170  -0.11597  0.0 8.0091 
175  -0.11597  0.0 8.0091];
                                    
%TEPHIN predicted max sinusoidal exponential coefficients
%used in form y = AcosB(x-C)+D  +  E(1-e^(-Fx))+G  -  H  +  model_max
%note that 0.0172 = 2*pi/365
Thermal.msid_tephin.cosexp = [4 0.0172 0 128 120 0.0007 108 220 117.2];

%TEPHIN forw sun bias characteristics
Thermal.msid_tephin.bias_max = 10;      % in degF
Thermal.msid_tephin.bias_slope = 1/3;   % in degF / hour
Thermal.msid_tephin.bias_pitch_cutoff = 65;     % in deg pitch

%TEPHIN slope during eclipses
Thermal.msid_tephin.ecl_slope = -8.0;     % in degF / hour

%TEPHIN benchmark temperatures for creation of TEPHIN max dwell time matrix
Thermal.msid_tephin.dwelltimematrix_temps = Thermal.msid_tephin.reference_limit + [0 2 4];
                                    
%3TRMTRAT thermal model parameters
%3TRMTRAT model default initial temperature
Thermal.msid_3trmtrat.default_initial_temperature = 30;

%3TRMTRAT yellow, red, & reference limits (reference draws a green line -
%-10000 for ref means don't plot the line)
Thermal.msid_3trmtrat.yellow_limit    = 50;
Thermal.msid_3trmtrat.red_limit       = 60;
Thermal.msid_3trmtrat.reference_limit = -10000;

%3TRMTRAT slope equations for each pitch range of the form  y = q1 * (x + q2) + q3
%NOTE: for the last bin (165-180), should repeat last equation so
%interpolation happens up to 170
Thermal.msid_3trmtrat.slope_equation = [45 -0.1191 0  4.3677
                                        55 -0.1178 0  4.1275
                                        65 -0.1191 0  3.4311
                                        75 -0.1147 0  2.9134
                                        85 -0.1136 0  2.0857
                                        95 -0.1012 0  0.0341
                                        105 -0.1068 0 -1.2425
                                        115 -0.0948 0 -1.9097
                                        125 -0.0969 0 -1.8193
                                        135 -0.1121 0 -2.1161
                                        145 -0.1201 0 -2.0721
                                        155 -0.1264 0 -2.0667
                                        165 -0.1077 0 -2.0628
                                        175 -0.1077 0 -2.0628];

%3TRMTRAT predicted max sinusoidal exponential coefficients
%used in form y = AcosB(x-C)+D  +  E(1-e^(-Fx))+G  -  H  +  model_max
Thermal.msid_3trmtrat.cosexp = [0 0 0 0 0 0 0 0 0];

%PM1THV1T thermal model parameters
%PM1THV1T model default initial temperature
Thermal.msid_pm1thv1t.default_initial_temperature = 140;

%PM1THV1T yellow, red, & reference limits (reference draws a green line -
%-10000 for ref means don't plot the line)
Thermal.msid_pm1thv1t.yellow_limit    = 160;
Thermal.msid_pm1thv1t.red_limit       = 240;
Thermal.msid_pm1thv1t.reference_limit = -10000;

%PM1THV1T slope equations for each pitch range of the form  y = q1 * (x + q2) + q3
%NOTE: for the last bin (165-180), should repeat last equation so
%interpolation happens up to 170
Thermal.msid_pm1thv1t.slope_equation = [45  -0.43291  2.0 65.6448
                                        50  -0.46792  2.0 69.5884
                                        55  -0.44624  2.0 66.9128
                                        60  -0.49799  2.0 74.3589
                                        65  -0.4827  2.0 70.5833
                                        70  -0.45489  2.0 65.8649
                                        75  -0.5135  2.0 73.3614
                                        80  -0.48478  2.0 66.9556
                                        85  -0.5025  2.0 67.1383
                                        90  -0.51826  2.0 68.2141
                                        95  -0.53697  2.0 70.1849
                                        100  -0.4303  2.0 57.5995
                                        105  -0.45809  2.0 61.7263
                                        110  -0.46984  2.0 62.8486
                                        115  -0.45962  2.0 61.2415
                                        120  -0.43274  2.0 56.908
                                        125  -0.57433  2.0 74.344
                                        130  -0.45299  2.0 57.7145
                                        135  -0.42638  2.0 52.7662
                                        140  -0.41026  2.0 48.917
                                        145  -0.41146  2.0 46.6921
                                        150  -0.39246  2.0 42.2665
                                        155  -0.42981  2.0 43.4539
                                        160  -0.42612  2.0 39.395
                                        165  -0.49086  2.0 42.1974
                                        170  -0.37703  -8.0 20.0549
                                        175  -0.4661  -8.0 17.3098];

%PM1THV1T predicted max sinusoidal exponential coefficients
%used in form y = AcosB(x-C)+D  +  E(1-e^(-Fx))+G  -  H  +  model_max
Thermal.msid_pm1thv1t.cosexp = [2 0.0172 0 193 58 0.0007 142 220 151.6];

%PM2THV1T thermal model parameters
%PM2THV1T model default initial temperature
Thermal.msid_pm2thv1t.default_initial_temperature = 140;

%PM2THV1T yellow, red, & reference limits (reference draws a green line -
%-10000 for ref means don't plot the line)
Thermal.msid_pm2thv1t.yellow_limit    = 160;
Thermal.msid_pm2thv1t.red_limit       = 240;
Thermal.msid_pm2thv1t.reference_limit = -10000;

%PM2THV1T slope equations for each pitch range of the form  y = q1 * (x + q2) + q3
%NOTE: for the last bin (165-180), should repeat last equation so
%interpolation happens up to 170
Thermal.msid_pm2thv1t.slope_equation = [45  -0.40281  5.8 61.4637
                                        50  -0.5948  5.8 90.9402
                                        55  -0.55767  5.8 86.5046
                                        60  -0.6347  5.8 97.113
                                        65  -0.54862  5.8 83.455
                                        70  -0.54731  5.8 81.9026
                                        75  -0.52287  5.8 76.094
                                        80  -0.54854  5.8 78.7526
                                        85  -0.63033  5.8 88.3228
                                        90  -0.61556  5.8 86.7344
                                        95  -0.59391  5.8 84.303
                                        100  -0.51831  5.8 73.9908
                                        105  -0.57016  5.8 81.5298
                                        110  -0.57437  5.8 82.198
                                        115  -0.52014  5.8 74.8028
                                        120  -0.51099  5.8 72.3638
                                        125  -0.57724  5.8 79.5539
                                        130  -0.50695  5.8 67.1014
                                        135  -0.48591  5.8 61.1116
                                        140  -0.48398  5.8 57.7415
                                        145  -0.48772  5.8 53.7489
                                        150  -0.48313  5.8 49.7645
                                        155  -0.51165  5.8 48.86
                                        160  -0.4762  5.8 40.986
                                        165  -0.55657  5.8 46.2355
                                        170  -0.35221  -4.2 15.8851
                                        175  -0.35923  -4.2 7.872];

%%PM2THV1T predicted max sinusoidal exponential coefficients
%used in form y = AcosB(x-C)+D  +  E(1-e^(-Fx))+G  -  H  +  model_max
Thermal.msid_pm2thv1t.cosexp = [2 0.0172 0 193 58 0.0007 142 213 155.1];

%PM2THV1T slope equations for each pitch range of the form  y = q1 * (x + q2) + q3
%NOTE: for the last bin (165-180), should repeat last equation so
%interpolation happens up to 170
Thermal.msid_1pin1at_acisi.slope_equation = [   45  -0.20065  0.0 7.8915
      50  -0.14861  0.0 6.0097
      55  -0.17886  0.0 6.4187
      60  -0.16128  0.0 5.5678
      65  -0.19834  0.0 6.048
      70  -0.25593  0.0 6.4868
      75  -0.25593  -5.3 6.4868
      80  -0.23722  -4.1 3.1771
      85  -0.19865  -5.1 2.0126
      90  -0.23522  -3.4 3.3157
      95  -0.16408  -2.5 1.7014
      100  -0.11381  -2.8 0.99833
      105  -0.15159  -3.2 1.4924
      110  -0.12668 -4.3 0.80175
      115  -0.16893 -3.9 1.9501 
      120  -0.16893  -4.1 1.9501
      125  -0.22214  -6.4 1.8833
      130  -0.15328  -4.4 1.9445
      135  -0.15739  -3.6 2.3663
      140  -0.13245  -5.4 1.3044
      145  -0.1556  -5.0 1.7971
      150  -0.1632  -4.4 2.1603
      155  -0.11611  -5.9 0.95481
      160  -0.14503  -4.9 1.7311
      165  -0.10579  -6.5 0.30088
      170  -0.10579  -9.2 0.30088 
      175  -0.10579  -8.8 0.30088 ];
                                    
Thermal.msid_1pin1at_aciss.slope_equation = Thermal.msid_1pin1at_acisi.slope_equation;

Thermal.msid_1pin1at_hrcs.slope_equation = [    45  -0.41148  0.0 7.3684
      50  -0.17209  0.0 3.0573
      55  -0.17209  0.0 3.0573 
      60  -0.17209  0.0 3.0573
      65  -0.21839  0.0 3.7324
      70  -0.58728  0.0 11.3885
      75  -0.58728  0.0 11.3885 
      80  -0.58728  0.0 11.3885 
      85  -0.58728  0.0 11.3885 
      90  -0.58728  0.0 11.3885
      95  -0.58728  0.0 11.3885 
      100  -0.58728  0.0 11.3885 
      105  -0.58728  0.0 11.3885 
      110  -0.58728  0.0 11.3885 
      115  -0.58728  0.0 11.3885 
      120  -0.41157  0.0 7.9467
      125  -0.20852  0.0 4.9462 
      130  -0.20852  0.0 4.9462 
      135  -0.20852  0.0 4.9462
      140  -0.18571  0.0 4.1254
      145  -0.095704  0.0 2.7562
      150  -0.273  0.0 6.5991
      155  -0.63314  0.0 16.017 
      160  -0.63314  0.0 16.017
      165  -0.39975  0.0 10.8654
      170  -0.39975  0.0 10.8654 
      175  -0.39975  0.0 10.8654 ];
                                    
Thermal.msid_1pin1at_hrci.slope_equation = [    45  -0.41148  -3.0 7.3684
      50  -0.17209  -3.0 3.0573
      55  -0.17209  -3.0 3.0573 
      60  -0.17209  -3.0 3.0573
      65  -0.21839  -3.0 3.7324
      70  -0.58728  -3.0 11.3885
      75  -0.58728  -3.0 11.3885 
      80  -0.58728  -3.0 11.3885 
      85  -0.58728  -3.0 11.3885 
      90  -0.58728  -3.0 11.3885
      95  -0.58728  -3.0 11.3885 
      100  -0.58728  -3.0 11.3885 
      105  -0.58728  -3.0 11.3885 
      110  -0.58728  -3.0 11.3885 
      115  -0.58728  -3.0 11.3885 
      120  -0.41157  -3.0 7.9467
      125  -0.20852  -3.0 4.9462 
      130  -0.20852  -3.0 4.9462 
      135  -0.20852  -3.0 4.9462
      140  -0.18571  -3.0 4.1254
      145  -0.095704  -3.0 2.7562
      150  -0.273  -3.0 6.5991
      155  -0.63314  -3.0 16.017 
      160  -0.63314  -3.0 16.017
      165  -0.39975  -3.0 10.8654
      170  -0.39975  -3.0 10.8654 
      175  -0.39975  -3.0 10.8654 ];

%%1PIN1AT predicted max sinusoidal exponential coefficients
%used in form y = AcosB(x-C)+D  +  E(1-e^(-Fx))+G  -  H  +  model_max
Thermal.msid_1pin1at.cosexp = [0.5 0.0172 0 128 25 0.0007 142 252 40.4];

%1PIN1AT model - ACIS chip information
Thermal.msid_1pin1at.chip_info.delta_t_perchip = [6 0; 5 -5; 4 -10; 3 -10; 2 -10; 1 -10; 0 -10];
Thermal.msid_1pin1at.chip_info.chiptempslope_decrease = -10000/(30*60);     % degC/sec
Thermal.msid_1pin1at.chip_info.chiptempslope_increase = +10000/(30*60);     % degC/sec

%Initial default 3TSCPOS value 
Thermal.msid_3tscpos.default_initial_position = 94000;

%PLINE constraints; ranges are deg pitch, time durations are in hours,
% first column is min temperatures in deg
Thermal.pline.constraint_grid = [   0   0   0   156     156     156        156;
                                    0   0   0   162     166     170        185;
                                    100 30  80  9+20/60 7+50/60 4+20/60    0;
                                    80  12  90  7       5+30/60 3          0;
                                    75  10  90  6+15/60 5+10/60 2+40/60    0;
                                    68  8   90  5+15/60 4+20/60 2+15/60    0;
                                    65  8   110 5       4+15/60 2          0];



%%% Begin Generated Text from SOT Python PSMC Characteristics %%%

% SOT VERSION 6



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


Thermal.msid_1pdeaat.model_defaults = struct( 'acis150' ,   28.03 , ... 
 'acis50' ,   54.19 , ... 
 'acis90' ,   26.98 , ... 
 'c1' ,  114.61 , ... 
 'c2' ,   11.36 , ... 
 'hrci150' ,   32.98 , ... 
 'hrci50' ,   38.54 , ... 
 'hrci90' ,   28.05 , ... 
 'hrcs150' ,   37.27 , ... 
 'hrcs50' ,   30.71 , ... 
 'hrcs90' ,   30.01 , ... 
 'u01' ,    6.04 , ... 
 'u01quad' ,   -0.60 , ... 
 'u12' ,    8.45  ); 

%PSMC average power for each state (fep_count, vid_board, clocking)
%['pk_ fep_count _ vid_board _ clocking', power_avg in watts]
Thermal.msid_1pdeaat.psmc_power = struct( 'pk_0_0_0',  15.00 , ... 
 'pk_1_0_0',  27.00 , ... 
 'pk_2_0_0',  42.00 , ... 
 'pk_3_0_0',  55.00 , ... 
 'pk_4_0_0',  69.00 , ... 
 'pk_5_0_0',  88.60 , ... 
 'pk_6_0_0',  96.60 , ... 
 'pk_0_1_0',  40.00 , ... 
 'pk_1_1_0',  58.30 , ... 
 'pk_2_1_0',  69.00 , ... 
 'pk_3_1_0',  80.00 , ... 
 'pk_4_1_0',  92.00 , ... 
 'pk_5_1_0', 112.30 , ... 
 'pk_6_1_0', 118.00 , ... 
 'pk_0_1_1',  40.00 , ... 
 'pk_1_1_1',  57.00 , ... 
 'pk_2_1_1',  72.00 , ... 
 'pk_3_1_1',  85.40 , ... 
 'pk_4_1_1',  99.20 , ... 
 'pk_5_1_1', 113.90 , ... 
 'pk_6_1_1', 129.00 , ... 
 'pk_0_0_1',  40.00 , ... 
 'pk_1_0_1',  57.00 , ... 
 'pk_2_0_1',  72.00 , ... 
 'pk_3_0_1',  85.40 , ... 
 'pk_4_0_1',  99.20 , ... 
 'pk_5_0_1', 113.90 , ... 
 'pk_6_0_1', 129.00  ); 


% Old 1PIN1AT yellow, red, & reference limits (reference draws a green line -"
% -10000 for ref means don't plot the line)"
Thermal.msid_1pin1at.yellow_limit    = 41;
Thermal.msid_1pin1at.red_limit       = 46;
Thermal.msid_1pin1at.reference_limit = 38.5;

% ACIS PSMC hardware yellow/red limits
Thermal.msid_1pdeaat.T_dea_yellow =  57.00 ; % 1PDEAAT yellow limit (degC)
Thermal.msid_1pdeaat.T_dea_red =  62.00; % 1PDEAAT red limit (degC)
Thermal.msid_1pin1at.T_pin_yellow =  41.00 ; % 1PIN1AT yellow limit (degC) 
Thermal.msid_1pin1at.T_pin_red =  46.00 ; % 1PIN1AT red limit (degC)  
% Mission planning margin from yellow limit reflecting accepted level of
% uncertainty (1%) in PSMC model predictions.
Thermal.msid_1pdeaat.T_dea_margin =  4.50; 
Thermal.msid_1pin1at.T_pin_margin =  4.50; 


%%%%%% End Generated Text from SOT Python PSMC Characteristics %%%%%%

