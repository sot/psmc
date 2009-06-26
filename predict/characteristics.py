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
# over the range 2009-01-01 - 2009-04-01
model_par = dict(acis150  =      29.0302,
                 acis50   =      56.0669,
                 acis90   =      29.7084,
                 c1       =      93.5736,
                 c2       =      12.9992,
                 hrci150 =  35.703,
                 hrci50  =  42.717,
                 hrci90  =  29.420,
                 hrcs150 =  39.351,
                 hrcs50  =  33.167,
                 hrcs90  =  31.769,
                 u01      =      5.64142,
                 u01quad  =     -1.09691,
                 u12      =      8.29004)


