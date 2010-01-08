=======================
PSMC temperatures check
=======================
.. role:: red


Summary
--------         
.. class:: borderless

====================  =============================================
Date start            2008:363:21:33:33.441
Date stop             2009:012:01:07:07.280
1PDEAAT status        OK (limit = 52.5 C)
1PIN1AT status        OK (limit = 36.5 C)
Run time              Fri Jan  8 13:39:04 2010 by jeanconn
Run log               `<run.dat>`_
Temperatures          `<temperatures.dat>`_
States                `<states.dat>`_
====================  =============================================

No 1PDEAAT Violations

No 1PIN1AT Violations

.. image:: 1pdeaat.png
.. image:: 1pin1at.png
.. image:: pow_sim.png

=======================
PSMC Model Validation
=======================

MSID quantiles
---------------

.. csv-table:: 
   :header: "MSID", "1%", "5%", "16%", "50%", "84%", "95%", "99%"
   :widths: 15, 10, 10, 10, 10, 10, 10, 10

   1PDEAAT,-2.11,-1.04,-0.16,1.18,2.61,3.50,4.36
   1PIN1AT,-1.94,-1.16,-0.54,1.01,2.59,3.51,4.21
   AOSARES1,-2.407,-0.098,-0.046,0.005,0.103,0.177,2.560
   POWER,-6.06,-3.14,-1.36,0.59,2.55,4.20,7.30
   TSCPOS,-1,-1,-1,0,0,1,1


Validation Violations
---------------------

.. csv-table:: 
   :header: "MSID", "Quantile", "Value", "Limit"
   :widths: 15, 10, 10, 10

   1PDEAAT,50,1.18,1.00
   AOSARES1,99,2.56,2.50




1PDEAAT
-----------------------
Red = telemetry, blue = model

.. image:: 1pdeaat_valid.png
.. image:: 1pdeaat_valid_hist_log.png
.. image:: 1pdeaat_valid_hist_lin.png

1PIN1AT
-----------------------
Red = telemetry, blue = model

.. image:: 1pin1at_valid.png
.. image:: 1pin1at_valid_hist_log.png
.. image:: 1pin1at_valid_hist_lin.png

AOSARES1
-----------------------
Red = telemetry, blue = model

.. image:: aosares1_valid.png
.. image:: aosares1_valid_hist_log.png
.. image:: aosares1_valid_hist_lin.png

POWER
-----------------------
Red = telemetry, blue = model

.. image:: power_valid.png
.. image:: power_valid_hist_log.png
.. image:: power_valid_hist_lin.png

TSCPOS
-----------------------
Red = telemetry, blue = model

.. image:: tscpos_valid.png
.. image:: tscpos_valid_hist_log.png
.. image:: tscpos_valid_hist_lin.png

