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

Configuring different analyse is critical to a workflow functioning correctly.
Bill of Materials analysis has a the base Configuration which is inherits a number of
methods for the Config and a Meta class for properties and setters. An analysis workflow
can use the BaseConfig directly or inherit the BaseConfigMethods and the MetaConfig to
customise the configuration parameters.

The base config includes a number of variables which can be used by BOM Analysis and
are covered in the other sections such as the MaterialsSelector, the defaults for the
Material and the Parameters, and a number of different working directories.

A configuration can also be loaded and dumped to a dictionary using the same method
names as the Engineering Components.

The Meta class which defines properies and setters
that can be used on the configuration without initialising it and our shared
like class properties.

Including properties and setters allows for better error handling and defaulting
of values. If a calculation is performed that called a translation but the
translator has not been defined within the configuration then a specific error
will be raised. If a plot directory is called then but it has not been defined
then it willd default to the working directory.

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

`An example of configuring the analyis is in <https://github.com/ukaea/bom_analysis/blob/main/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__

--------------------
Running Analysis
--------------------
In order to help with running analysis automatically,
a series of classes are included. 

 * Solver - automatically runs analysis steps
 * Step - defines the analysis steps
 * Framework - populates the required classes from dictionary

The solver contains an ordered dictionary which should be
made up of the steps that the analysis will go through. It can be
populated manually or build from a settings file.

As with the engineering objects the solver can be written
to a dictionary using the same method names.

The solver implemented in BOM Analysis is made up
of a series of steps ran in linear order. Each step
requires the class (not initialised) to be initialised,
the method within the class that will be run plus and
arguments or key word arguments. The solve function
can then be run to execute the step.

The framework offers an automated way of populating configurations,
translators, settings, and parsing skeletons uting dictionaries.
Following poplulation of the various different required information
it can then getnerate the bill of materials and solve the analysis
workflow.

The solver and the configuration are stored as class variables.

See the :obj:`~bom_analysis.solver.Solver`, :obj:`~bom_analysis.solver.Step`, :obj:`~bom_analysis.build.Framework` for docstrings.

`An example of configuring the analyis is in <https://github.com/ukaea/bom_analysis/blob/main/examples/example_3%20-%20Other%20Useful%20Classes.ipynb>`__
