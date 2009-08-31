#!/usr/bin/env python

"""
========================
run_psmc_daily
========================

This code calls psmc_check for daily trending.

"""

import sys
import os
import glob
import logging
import datetime
import re
import time
import mx.DateTime

from Chandra.Time import DateTime

PSMC_CHECK_EXE = os.path.join(os.environ['SKA'], 'bin', 'psmc_check')
TASK_DATA = os.path.join(os.environ['SKA'], 'data', 'psmc', 'daily')

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--run_start_time",
                      default= DateTime(time.time(), format='unix').date,
                      help="Reference start time for end of telemetry range")
    parser.add_option("--telem_days",
                      type='float',
                      default= 21.0,
                      help="Number of days of telemetry to retrieve")
    parser.add_option("--data_dir",
                      default=TASK_DATA,
                      help="parent directory for data by year/day")
    parser.add_option("--traceback",
                      default=True,
                      help='Enable tracebacks')
    parser.add_option("--verbose",
                      type='int',
                      default=1,
                      help="Verbosity (0=quiet, 1=normal, 2=debug)")
    opt, args = parser.parse_args()
    return opt, args

def main(opt):

    run_time_date = DateTime(opt.run_start_time).date
    run_time_mx = DateTime(opt.run_start_time).mxDateTime
    day_dir = os.path.join( opt.data_dir, "%s" % run_time_mx.year, "%s" % run_time_mx.day_of_year )
    if not os.path.exists(day_dir):
        os.makedirs(day_dir)
    os.system("%s --run_start_time %s --days %s --outdir %s" 
              % ( PSMC_CHECK_EXE, run_time_date, opt.telem_days, day_dir))


#    if not os.path.exists(opt.outdir):
#        os.mkdir(opt.outdir)
#
#    config_logging(opt.outdir, opt.verbose)


def config_logging(outdir, verbose):
    """Set up file and console logging.
    See http://docs.python.org/library/logging.html#logging-to-multiple-destinations
    """
    loglevel = { 0: logging.CRITICAL,
                 1: logging.INFO,
                 2: logging.DEBUG }.get(verbose, logging.INFO)
    logging.basicConfig(level=loglevel,
                        format='%(message)s',
                        filename=os.path.join(outdir, 'run.dat'),
                        filemode='w')

    console = logging.StreamHandler()
    console.setLevel(loglevel)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    opt, args = get_options()
    try:
        main(opt)
    except Exception, msg:
        if opt.traceback:
            raise
        else:
            print "ERROR:", msg
            sys.exit(1)
