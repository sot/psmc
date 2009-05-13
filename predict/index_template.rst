=======================
PSMC temperatures check
=======================
.. role:: red

{% if proc.errors %}
Processing Errors
-----------------
.. class:: red
{% endif %}

Summary
--------         
.. class:: borderless

====================  =============================================
Date start            {{proc.datestart}}
Date stop             {{proc.datestop}}
1PDEAAT status        {%if viols.dea%}:red:`NOT OK`{% else %}OK{% endif%} (limit = {{proc.dea_limit|floatformat:1}} C)
1PIN1AT status        {%if viols.dea%}:red:`NOT OK`{% else %}OK{% endif%} (limit = {{proc.pin_limit|floatformat:1}} C)
{% if opt.loaddir %}
Load directory        {{opt.loaddir}}
{% endif %}
Run time              {{proc.run_time}} by {{proc.run_user}}
Run log               `<run.dat>`_
Temperatures          `<temperatures.dat>`_
States                `<states.dat>`_
====================  =============================================

{% if viols.dea %}
1PDEAAT Violations
-------------------
=====================  =====================  ==================
Date start             Date stop              Max temperature
=====================  =====================  ==================
{% for viol in viols.dea %}
{{viol.datestart}}  {{viol.datestop}}  {{viol.maxtemp|floatformat:2}}
{% endfor %}
=====================  =====================  ==================
{% else %}
No 1PDEAAT Violations
{% endif %}

{% if viols.pin %}
1PIN1AT Violations
-------------------
=====================  =====================  ==================
Date start             Date stop              Max temperature
=====================  =====================  ==================
{% for viol in viols.pin %}
{{viol.datestart}}  {{viol.datestop}}  {{viol.maxtemp|floatformat:2}}
{% endfor %}
=====================  =====================  ==================
{% else %}
No 1PIN1AT Violations
{% endif %}

.. image:: {{plots.dea.filename}}
.. image:: {{plots.pin.filename}}
.. image:: {{plots.pow_sim.filename}}

=======================
PSMC Model Validation
=======================

MSID quantiles
---------------

.. csv-table:: 
   :header: "MSID", "1%", "5%", "16%", "50%", "84%", "95%", "99%"
   :widths: 15, 10, 10, 10, 10, 10, 10, 10

{% for plot in plots_validation %}
{% if plot.quant01 %}
   {{plot.msid}},{{plot.quant01}},{{plot.quant05}},{{plot.quant16}},{{plot.quant50}},{{plot.quant84}},{{plot.quant95}},{{plot.quant99}}
{% endif %}
{% endfor%}

{% for plot in plots_validation %}
{{ plot.msid }}
-----------------------
.. image:: {{plot.lines}}
.. image:: {{plot.histlog}}
.. image:: {{plot.histlin}}

{% endfor %}
