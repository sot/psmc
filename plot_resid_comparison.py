#!/usr/bin/env python

"""Overplot the residuals for two runs of psmc_check.py for regression test purposes."""

import os
import numpy
import matplotlib.pyplot as plt
import pickle

def get_options():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] dir1 dir2")

    opt, args = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        sys.exit(0)

    return opt, args

opt, args = get_options()
dir1 = args[0]
dir2 = args[1]

dat1 = pickle.load(open(os.path.join(dir1, 'validation_data.pkl')))
dat2 = pickle.load(open(os.path.join(dir2, 'validation_data.pkl')))

plt.rc("axes", labelsize=10, titlesize=10)
plt.rc("xtick", labelsize=10)
plt.rc("ytick", labelsize=10)
plt.rc("font", size=10)
plt.rc("legend", fontsize=10)

bins1 = numpy.arange(-10, 10, 0.4)
bins2 = bins1 + 0.2
plt.figure(figsize=(3.5,2.5))
plt.clf()
plt.hist(dat1['tlm']['1pdeaat'] - dat1['pred']['1pdeaat'], bins=bins1, facecolor='r')
plt.hist(dat2['tlm']['1pdeaat'] - dat2['pred']['1pdeaat'], bins=bins2, facecolor='b', alpha=0.7)
plt.title('Residual distribution (old=red new=blue)')
plt.xlabel('Data - model (degC)')
plt.subplots_adjust(bottom=0.17, top=0.84, left=0.17)
plt.savefig('hist_compare_lin.png')

plt.clf()
plt.hist(dat1['tlm']['1pdeaat'] - dat1['pred']['1pdeaat'], bins=bins1, facecolor='r', log=True)
plt.hist(dat2['tlm']['1pdeaat'] - dat2['pred']['1pdeaat'], bins=bins2, facecolor='b', alpha=0.7, log=True)
plt.title('Residual distribution (old=red new=blue)')
plt.xlabel('Data - model (degC)')
plt.subplots_adjust(bottom=0.17, top=0.84)
plt.savefig('hist_compare_log.png')


    
