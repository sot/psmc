#!/usr/bin/env python

import os
import sys
import numpy as np
import re
import shutil
import pkg_resources
pkg_resources.require('Ska.Numpy')
import Ska.Numpy
import Ska.Table
from Chandra.Time import DateTime

#Matplotlib setup
# Use Agg backend for command-line (non-interactive) operation
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import Ska.Matplotlib
from Ska.Matplotlib import plot_cxctime, pointpair

def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--py_dir",
                      default='py',
                      help="directory containing psmc_check output")
    parser.add_option("--mat_dir",
                      default='mat',
                      help="matlab output dir")
    parser.add_option("--title",
                      help="Output title string")
    parser.add_option("--outdir",
                      default='out',
                      help="output directory")

    opt, args = parser.parse_args()

    return opt, args

#class option(object):
#    def __init__(self, **kwargs):
#        self.__dict__.update(kwargs)
#
#opt = option(
#    py_dir = 'py_dec2908b',
#    mat_dir = 'mat_b_dec2908b',
#    outdir='test',)


def rst_to_html(opt):
    """Run rst2html.py to render index.rst as HTML
    (borrowed from psmc_check, proc stuff cut out )
    
    """

    # First copy CSS files to outdir
    import Ska.Shell
    import docutils.writers.html4css1
    dirname = os.path.dirname(docutils.writers.html4css1.__file__)
    shutil.copy2(os.path.join(dirname, 'html4css1.css'), opt.outdir)
#    shutil.copy2(os.path.join(TASK_DATA, 'psmc_check.css'), opt.outdir)
    shutil.copy2('psmc_check.css', opt.outdir)
    spawn = Ska.Shell.Spawn(stdout=None)
    infile = os.path.join(opt.outdir, 'index.rst')
    outfile = os.path.join(opt.outdir, 'index.html')
    status = spawn.run(['rst2html.py',
                        '--stylesheet-path=%s' % os.path.join(opt.outdir, 'psmc_check.css'),
                        infile, outfile])
    # Remove the stupid <colgroup> field that docbook inserts.  This
    # <colgroup> prevents HTML table auto-sizing.
    del_colgroup = re.compile(r'<colgroup>.*?</colgroup>', re.DOTALL)
    outtext = del_colgroup.sub('', open(outfile).read())

    open(outfile, 'w').write(outtext)


def main(opt):  
    """
    Compare Matlab and Python PSMC model temperatures and states for a set of products.  
    Models are manually run outside this tool with output placed into directories used
    as source data for this tool.  

    Example, DEC2809B products:

    Running python model:

      psmc_check --oflsdir /data/mpcrit1/mplogs/2008/DEC2908/oflsb --outdir py_dec2908b

    Running Matlab model:

      Open Matlab
      Open MCC
      Import a Backstop or DOT from DEC2908b
      Import SIM and Chip information from the menu
      Change to 1PDEAAT view
      Export Plot to Text file ( the one labeled "new method")
        ( save as 'temperatures.dat' in a directory like mat_dec2908b )
      Export PSMC States
        ( save as 'states.dat' in a directory like mat_dec2908b )
    
    """
    
    opt, args = get_options()
    if not os.path.exists(opt.outdir):
        os.mkdir(opt.outdir)
    temp_file = 'temperatures.dat'
    state_file = 'states.dat'
    # read the temperatures from the ascii files from each method
    py_temps = Ska.Table.read_ascii_table(os.path.join(opt.py_dir, temp_file))
    mat_temps = Ska.Table.read_ascii_table(os.path.join(opt.mat_dir, temp_file))
    py_states = Ska.Table.read_ascii_table(os.path.join(opt.py_dir, state_file))
    mat_states = Ska.Table.read_ascii_table(os.path.join(opt.mat_dir, state_file))
    # use the time range from the matlab processing for comparisons
    range_py = py_temps[( py_temps['date'] >= mat_temps[0]['Time']) 
                        & ( py_temps['date'] <= mat_temps[-1]['Time'])]


    # note that the mat states have the dates labeled tstart (not chandra secs),
    # so the searchsorted compares range_py['date'] to mat_states.tstart
    # the searchsorted indices are still shifted one to the right of the
    # answer we want, so subtract 1
    mat = { '1pdeaat' : 
            Ska.Numpy.interpolate(mat_temps['1PDEAAT Prediction (degC)'],
                                  DateTime(mat_temps['Time']).secs,
                                  range_py['time']
                                  ),
            '1pin1at' :
                Ska.Numpy.interpolate(mat_temps['1PIN1AT Prediction'],
                                      DateTime(mat_temps['Time']).secs,
                                      range_py['time']
                                      ),
            'pitch' :
                mat_states[ np.searchsorted( mat_states.tstart, 
                                             range_py['date'] ) - 1]['pitch'],
            'power':
                mat_states[ np.searchsorted( mat_states.tstart, 
                                             range_py['date'] ) - 1]['power'],
            'simpos':
                mat_states[ np.searchsorted( mat_states.tstart, 
                                             range_py['date'] ) - 1]['simpos'],

    }

    py = { '1pdeaat' : range_py['1pdeaat'],
           '1pin1at' : range_py['1pin1at'],
            'pitch' :
               py_states[ np.searchsorted( py_states.datestart, 
                                           range_py['date'] ) - 1]['pitch'],
           'power':
               py_states[ np.searchsorted( py_states.datestart, 
                                           range_py['date'] ) - 1]['power'],
           'simpos':
               py_states[ np.searchsorted( py_states.datestart, 
                                           range_py['date'] ) - 1]['simpos'],
    }

    # borrow some more code from psmc_check with regard to format and scaling
    scales = {'tscpos': 1000.} 

    fmts = {'1pdeaat': '%.2f',
            '1pin1at': '%.2f',
            'pitch': '%.3f',
            'power': '%.2f',
            'simpos': '%d'}  

    ylabels = {'1pdeaat': 'Deg C', 
               '1pin1at': 'Deg C',
               'pitch': 'Deg', 
               'power': 'W',
               'simpos': 'steps'}


    # but manually define the plot limits for the "overplot" data plots
    msidlimits = {'1pdeaat' : (None,None),
                  '1pin1at' : (None,None),
                  'pitch' : (40,160),
                  'power' : (35,135),
                  'simpos' : (-110000,110000)}

    plots = []
    for msid in sorted(mat.keys()):
        plot = dict(msid=msid.upper())
        scale = scales.get(msid, 1.0)
        plt.figure(figsize=(8,4))
        Ska.Matplotlib.plot_cxctime( range_py['time'], 
                                     mat[msid], 
                                     color='b',
                                     marker='.',
                                     linestyle='-.',
                                     markersize=2,
                                     label='matlab')
        Ska.Matplotlib.plot_cxctime( range_py['time'], 
                                     py[msid], 
                                     color='r',
                                     markersize=2,
                                     linestyle='-',
                                     label='python')

        plt.ylabel('%s (%s)' % ( msid, ylabels[msid] ))
        #     plt.legend(('matlab', 'python'), 'upper left')
        plt.title('Matlab & Python Models (matlab=blue, python=red)')
        plt.ylim(msidlimits[msid])
        filename = '%s_overplot.png' % msid
        plt.savefig(os.path.join(opt.outdir, filename)) 
        plt.clf()
        plot['overplot'] = filename

        diff = py[msid] - mat[msid]

        Ska.Matplotlib.plot_cxctime( range_py['time'], 
                                     diff,
                                     color='b',
                                     )
        plt.ylabel('%s Residuals (%s)' % ( msid, ylabels[msid] ))
    #     plt.legend(('matlab', 'python'), 'upper left')
        plt.title('Python - Matlab Residuals')
        filename = '%s_resid.png' % msid
        plt.savefig(os.path.join(opt.outdir, filename)) 
        plt.clf()
        plot['resid'] = filename


        for histscale in ('log', 'lin'):
            fig = plt.figure(figsize=(4,3))
            fig.clf()
            ax = fig.gca()
            ax.hist(diff / scale, bins=50, log=(histscale=='log'))
            ax.set_title(msid.upper() + ' residuals: python - matlab')
    #        ax.set_xlabel(labels[msid])
            fig.subplots_adjust(bottom=0.18)
            filename = '%s_valid_hist_%s.png' % (msid, histscale)
            outfile = os.path.join(opt.outdir, filename)
     #       logging.info('Writing plot file %s' % outfile)
            fig.savefig(outfile)
            plot['hist' + histscale] = filename
        plots.append(plot)  


    quantiles = (1, 5, 16, 50, 84, 95, 99)
    # store lines of quantile table in a string and write out later
    quant_table = ''
    quant_head = "MSID"
    for quant in quantiles:
        quant_head += ",quant%d" % quant
    quant_table += quant_head + "\n"
    tables = []
    for msid in sorted(mat.keys()):
        # Make quantiles
        table = dict(msid=msid.upper())
        diff = np.sort(py[msid] - mat[msid])
        quant_line = "%s" % msid
        for quant in quantiles:
            quant_val = diff[(len(diff) * quant) // 100]
            quant_line += (',' + "%5.2f" % quant_val)
            table['quant%02d' % quant] = fmts[msid] % quant_val
        quant_table += quant_line + "\n"
        tables.append(table)
    quant_filename = os.path.join(opt.outdir, 'quantiles.csv')
    quant_file = open(quant_filename, 'w')
    quant_file.write(quant_table)
    quant_file.close()

    # Django setup (used for template rendering)
    import django.template
    import django.conf

    try:
        django.conf.settings.configure()
    except RuntimeError, msg:
        print msg

    outfile = os.path.join(opt.outdir, 'index.rst')
    django_context = django.template.Context({'opt': opt,
                                              'tables': tables,
                                              'plots': plots,
                                              })

    index_template_file = 'comparison_template.rst'
    index_template = open(index_template_file).read()
    index_template = re.sub(r' %}\n', ' %}', index_template)
    template = django.template.Template(index_template)
    open(outfile, 'w').write(template.render(django_context))
    rst_to_html(opt)


if __name__ == '__main__':
    opt, args = get_options()
    try:
        main(opt)
    except Exception, msg:
        raise
