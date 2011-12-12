VERSION = 7

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
              (6, 1, 1, 129.0),
              (0, 0, 1, 40.0),    # These last 7 states only occur
              (1, 0, 1, 57.0),    # for a short time due to 
              (2, 0, 1, 72.0),    # missing stop science at end of
              (3, 0, 1, 85.4),    # previous load.
              (4, 0, 1, 99.2),
              (5, 0, 1, 113.9),
              (6, 0, 1, 129.0))

# ACIS PSMC hardware yellow/red limits
T_dea_yellow = 57.0                     # 1PDEAAT yellow limit (degC)
T_dea_red = 62.0                        # 1PDEAAT red limit (degC)
T_pin_yellow = 41.0                     # 1PIN1AT yellow limit (degC)
T_pin_red = 46.0                        # 1PIN1AT red limit (degC)

# Mission planning margin from yellow limit reflecting accepted level of
# uncertainty (1%) in PSMC model predictions.
T_dea_margin = 4.5
T_pin_margin = 4.5                 

# Based on simplex fit of both 1pdeaat and 1pin1at for 200 days before
# 2010:001.  All params except u01quad were free.
model_par = dict(
                 acis150 =  28.532,
                 acis50  =  55.127,
                 acis90  =  26.996,
                 c1      = 113.695,
                 c2      =  12.024,
                 hrci150 =  33.062,
                 hrci50  =  42.657,
                 hrci90  =  30.204,
                 hrcs150 =  37.863,
                 hrcs50  =  31.263,
                 hrcs90  =  30.135,
                 u01     =   5.942,
                 u01quad =  -0.599,
                 u12     =   8.502,
                )

# validation limits
# 'msid' : (( quantile, absolute max value ))
validation_limits = { '1PDEAAT' :  ((1,5.5),
                                   (50,1.0),
                                   (99, 5.5)),
                      '1PIN1AT' :  ((1, 5.5),
                                    (99, 5.5)),
                      'AOSARES1' : ((1, 2.5),
                                    (99, 2.5),),
                      'POWER':     ((1, 10.0),
                                    (99, 10.0),),
                      'TSCPOS' :   ((1, 2.0),
                                    (99, 2.0),) }

if __name__ == '__main__':
    print VERSION
