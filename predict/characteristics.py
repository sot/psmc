VERSION = '0.04'

# PSMC average power for each state (fep_count, vid_board, clocking)
# [fep_count, vid_board, clocking, power_avg]
psmc_power = ((0, 0, 0, 15.0),
              (1, 0, 0, 27.0),
              (2, 0, 0, 42.0),
              (3, 0, 0, 55.0),
              (4, 0, 0, 69.0),
              (5, 0, 0, 88.6),
              (6, 0, 0, 96.6),
              (0, 1, 0, 40.0),
              (1, 1, 0, 58.3),
              (2, 1, 0, 69.0),
              (3, 1, 0, 80.0),
              (4, 1, 0, 92.0),
              (5, 1, 0, 112.3),
              (6, 1, 0, 118.0),
              (0, 1, 1, 40.0),
              (1, 1, 1, 57.0),
              (2, 1, 1, 72.0),
              (3, 1, 1, 85.4),
              (4, 1, 1, 99.2),
              (5, 1, 1, 113.9),
              (6, 1, 1, 129.0))

# ACIS PSMC hardware yellow/red limits
T_dea_yellow = 57.0                     # 1PDEAAT yellow limit (degC)
T_dea_red = 62.0                        # 1PDEAAT red limit (degC)
T_pin_yellow = 41.0                     # 1PIN1AT yellow limit (degC)
T_pin_red = 46.0                        # 1PIN1AT red limit (degC)

# Mission planning margin from yellow limit reflecting accepted level of
# uncertainty (1%) in PSMC model predictions.
T_dea_margin = 4.5
T_pin_margin = 4.5                 

# Based on levmar fit of both 1pdeaat and 1pin1at
# for 180 days before 2009:151:23:58:53.816
offset = 1.7
model_par = dict(acis150 =  28.948-offset,
                 acis50  =  55.302-offset,
                 acis90  =  27.870-offset,
                 c1      =  97.303,
                 c2      =  12.999,
                 hrci150 =  37.773-offset,
                 hrci50  =  40.637-offset,
                 hrci90  =  27.804-offset,
                 hrcs150 =  40.054-offset,
                 hrcs50  =  34.032-offset,
                 hrcs90  =  30.542-offset,
                 u01     =   5.404,
                 u01quad =  -0.438,
                 u12     =   8.404,
                )

# validation limits
# 'msid' : (( quantile, absolute max value ))
validation_limits = { '1PDEAAT' :  ((1,5.5),
                                   (50,1.0),
                                   (99, 5.5)),
                      '1PIN1AT' :  ((1, 5.5),
                                   (99, 5.5)),
                      'AOSARES1' : ((1, 2.5),),
                      'POWER':     ((1, 8.0),),
                      'TSCPOS' :   ((1, 2.0 ),) }
