====================
Analysis
====================

To aid with the using bill of materials for analysis a number of 
key features are included that allows an analysis to be configured,
ran, and logged.

--------------------
Logging
--------------------
A logger has been included within the BOM analysis which will write a log 
file to the working directory with INFO, DEBUG, WARNING, and ERROR levels.

This allows for multiple analysis to write to the same log file and is 
easy to import:

.. code-block:: python

    from bom_analysis import run_log
    run_log.info("Assuming bilinear material")

--------------------
Configuring Analysis
--------------------
.. _configure analysis:

.. automodule:: bom_analysis.base.MetaConfig
                :noindex:

An example of setting up a custom Configuration is given:

.. code-block:: python

    from bom_analysis.base import BaseConfigMethods, MetaConfig
    
    class NewMetaConfig(MetaConfig):
        @property
        def default_element_type(cls):
            if cls.analysis_type == "3D":
                return "C3D8"
            elif cls.analysis_type == "2D":
                return "CPE4"

    class MyNewConfig(BaseConfigMethods, metaclass=NewMetaConfig):
        analysis_type="2D"

The new config can then be called without initialisation and any calculation
could check the analysis type and return the appropriate default element type.

See the :obj:`bom_analysis.base.BaseConfigMethods` for docstrings.

`An example of configuring the analyis. <https://github.com/ukaea/bom_analysis/blob/main/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__

--------------------
Running Analysis
--------------------
In order to help with running analysis automatically,
a series of classes are included. 

 * Solver - automatically runs analysis steps
 * Step - defines the analysis steps
 * Framework - populates the required classes from dictionary

.. automodule:: bom_analysis.solver.Solver
                :noindex:

.. automodule:: bom_analysis.solver.Step
                :noindex:

.. automodule:: bom_analysis.build.Framework
                :noindex:

The solver and the configuration are stored as class variables.

See the :obj:`~bom_analysis.solver.Solver`, :obj:`~bom_analysis.solver.Step`, :obj:`~bom_analysis.build.Framework` for docstrings.

`An example of running the analyis. <https://github.com/ukaea/bom_analysis/blob/main/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__
