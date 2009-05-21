.. psmc documentation master file, created by

Chandra PSMC model tools
==================================

This suite of tools provides the tools to use and maintain the Chandra ACIS
PSMC model.  The key elements are:

  - ``psmc_check.py``: Thermal check of command loads and validate PSMC model against recent telemetry
  - ``psmc_calibrate.py``: Calibrate PSMC model coefficients
  - ``twodof.py``: Actual PSMC model code
  - ``characteristics.py``: Characteristics used in model evaluation

The PSMC tools depend on Sybase tables and in particular the commanded states database
which is accessed primarily via the Chandra.cmd_states_ module.

.. _Chandra.cmd_states: ../pydocs/Chandra.cmd_states.html

psmc_check
========================

Overview
-----------
This code generates backstop load review outputs for checking the ACIS
PSMC temperatures 1PIN1AT and 1PDEAAT.  It also generates PSMC model validation
plots comparing predicted values to telemetry for the previous three weeks.

Command line options
---------------------
===================== ====================================== ===================
Option                Description                            Default           
===================== ====================================== ===================
-h, --help            show this help message and exit                           
--outdir=OUTDIR       Output directory                       out         
--oflsdir=OFLSDIR     Load products OFLS directory           None               
--power=POWER         Starting PSMC power (watts)            From telemetry     
--simpos=SIMPOS       Starting SIM-Z position (steps)        From telemetry     
--pitch=PITCH         Starting pitch (deg)                   From telemetry     
--T_dea=T_DEA         Starting 1pdeaat temperature (degC)    From telemetry     
--T_pin=T_PIN         Starting 1pin1at temperature (degC)    From telemetry     
--dt=DT               Time step for model evaluation (sec)   32.8               
--days=DAYS           Days of validation data (days)         21                 
--traceback=TRACEBACK Enable tracebacks                      True
--verbose=VERBOSE     Verbosity (0=quiet, 1=normal, 2=debug) 1 (normal)
===================== ====================================== ===================

The model starting parameters (temperature and spacecraft state) can be
specified in one of two ways:

 - Provide all of the ``power``, ``simpos``, ``pitch``, ``T_dea``, and ``T_pin``
   command line options corresponding to the expected state at the
   load start time.  This may be necessary in the event of complex replan
   situations where the second option fails to capture the correct starting
   state.  In this case the ``cmd_states`` table is not used.

 - Provide none of the above command line options.  In this case the tool
   will propagate forward from a 5-minute average of the last available
   telemetry using the ``cmd_states`` table.  This table contains expected
   commanding from the approved command loads in the operations database.  This
   is the default usage.

Usage
--------

The typical way to use the load review tool =psmc_check.py= is via the script
launcher =/proj/sot/ska/bin/psmc_check=.  This script sets up the Ska runtime
environment to ensure access to the correct python libraries.  This must be run
on a 64-bit linux machine. Presently the OS should be Fedora Core 8; other
configurations may fail.

::

 /proj/sot/ska/bin/psmc_check --outdir=out --oflsdir=/data/mpcrit1/mplogs/2009/MAY1809/oflsb
 /proj/sot/ska/bin/psmc_check --simpos -99616 --ra 30 --dec 40 --roll 50 --T_dea 40 --T_pin 30 --power 80

Tools
====================

.. toctree::
   :maxdepth: 2

   psmc_check
   twodof

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

