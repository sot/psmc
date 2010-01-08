----------------------------
{{ opt.title }}
----------------------------


Model Difference Quantiles
--------------------------

.. csv-table:: 
   :header: "MSID", "1%", "5%", "16%", "50%", "84%", "95%", "99%"
   :widths: 15, 10, 10, 10, 10, 10, 10, 10

{% for msidline in tables %}
{% if msidline.quant01 %}
   {{msidline.msid}},{{msidline.quant01}},{{msidline.quant05}},{{msidline.quant16}},{{msidline.quant50}},{{msidline.quant84}},{{msidline.quant95}},{{msidline.quant99}}
{% endif %}
{% endfor%}


{% for plot in plots %}
{{ plot.msid }}
-----------------------

.. image:: {{plot.overplot}}

{% if plot.resid %}
.. image:: {{plot.resid}}
{% endif %}

.. image:: {{plot.histlog}}
.. image:: {{plot.histlin}}

{% endfor %}
