====================
Analysis
====================

To aid with the using bill of materials for analysis a number of
key features are included that allows an analysis to be configured,
ran, and logged.

--------------------
Logging
--------------------
A logger has been included within the BOM analysis which will write log
files to the working directory with INFO, DEBUG, WARNING, and ERROR levels
and time stamp them. This log file is called base.log as is intended to
provide a complete list of the logs when BOM analysis is used in a parameter
sweep. The base.log has a maximum file size before deleting information
contained within. There is a INFO level and above log that is written
to the temporary directory (defined by BaseConfig.temp_dir) which is meant
to capture information about assumptions of an analysis within a run folder
of the parameter sweep, this log is called run.log and is changed using
the change_handler method in bom_analysis.utils. Additionally, there is
a WARNING level console handler for display within the console.

Information can easily be added to the log file and will be handled by
the appropriate handler to be written to the location based on the
level assigned:

.. code-block:: python

    from bom_analysis import run_log
    run_log.info("Assuming bilinear material")

--------------------
Configuring Analysis
--------------------
.. _configure analysis:

.. automodule:: bom_analysis.base.BaseConfigMethods
.. automodule:: bom_analysis.base.MetaConfig

An example of setting up a custom Configuration is
given.

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

`An example of configuring the analyis is in <https://git.ccfe.ac.uk/step/invesselcomponents/outboardblanket/bom_analysis/-/blob/development/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__

--------------------
Running Analysis
--------------------
In order to help with running analysis automatically,
a series of classes are included.

 * Solver - automatically runs analysis steps
 * Step - defines the analysis steps
 * Framework - populates the required classes from dictionary

.. automodule:: bom_analysis.solver.Solver

.. automodule:: bom_analysis.solver.Step

.. automodule:: bom_analysis.build.Framework

See the :obj:`~bom_analysis.solver.Solver`, :obj:`~bom_analysis.solver.Step`, :obj:`~bom_analysis.build.Framework` for docstrings.

`An example of configuring the analyis is in <https://git.ccfe.ac.uk/step/invesselcomponents/outboardblanket/bom_analysis/-/blob/development/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__
