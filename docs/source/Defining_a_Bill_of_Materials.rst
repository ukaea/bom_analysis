===============================
Defining a Bill of Materials
===============================

The definition of a bill of materials is required and can be done manually
by assembling components and assemblies, by parsing together a set of .json/dictionary, 
or by loading in a previous BOM from a skeleton.

-------------------
The Skeleton
-------------------

A key feature of the Bill of Materials analysis is that objects
can be written and read from a serialisable dictionary. The dictionary
of the bill of materials is known as the Skeleton and a read and write to
skeleton feature is included in the parent BaseClass of all bill of
material objects.

The skeleton is key for transfering information. It can either be built
by parsing together a set of dictionaries and then read to create a bill
of materials or written as an output of a pre-assembled Bill of Materials.

The skeleton offers a number of benefits, it is generally the primary output
of analysis ran on the bill of materials, therefore, recording the state of
the inputs for that analysis (this can be particularly important for transfering
data in between Model Based System Engieering workflows).

-----------------------------------------
Importing and Exporting Bill of Materials
-----------------------------------------
Importing and exporting components in the bill of materials 
takes place with the from_dict and to_dict method, respectively. 

The dictionary of the Bill of Materials that are input and output
are known as skeletons (because they are fleshed out into Engineering Objects).

The skeleton is a flat structure, so it is necessary to tell it which 
reference is at the top of the hierarchy.

.. code-block:: python

    flange_assembly = Assembly(ref="P00000")
    skeleton = flange_assembly.to_dict()
    new_flange_assembly = Assembly().from_dict(skeleton, ref="P00000")

See the :obj:`bom_analysis.bom.Assembly.to_dict` for docstrings.

`A worked example of using the Importing and Exporting can be found here <https://github.com/ukaea/bom_analysis/blob/main/examples/example_1%20-%20Loading_a_Bill_of_Materials.ipynb>`__


--------------------
Parsing Skeleton
--------------------
Parsing a skeleton is a way of building a skeleton without
building the bill of materials. It can help speed up the
creation of new BOM but, as it parsers a number of files,
operates mostly with .json and is therefore not object orientated.

The skeleton can be parsed from a a config and setting dictionary
which contains all the information needed. The config dictionary
can also be read into the Configuration class.

The parsers can be found in the parser.py section of BOM analysis.

See the :obj:`bom_analysis.parsers.SkeletonParser` for docstrings.

`A worked example of using the Parsing can be found here <https://github.com/ukaea/bom_analysis/blob/main/examples/extra_example_0%20-%20Creating_a_Skeleton_from_Dictionaries.ipynb>`__

-------------------
Plotting Hierarchy
-------------------
The bill of materials hierarchy can be plotted in order to visualises the layout, particularly
useful for checking the structure is correct.

.. code-block:: python

    bolt_and_nut.plot_hierarchy()
    >> P12345 __ P10154
    >>        |_ P50501

This prints a treelib tree of the BOM.

See the :obj:`bom_analysis.bom.Assembly.plot_hierarchy` for docstrings.

--------------------
Classes from Strings
--------------------

On of the requirements for a skeleton is to allow rebuilding of a bill of materials from
it. To do this, serialisable strings must be read as input. In order to capture the classes 
used the path to a class (for example RaBBIT.Assembly) is written to the skeleton and can 
then be converted by class_factory or class_from_strings in utils.

 * class_from_strings - returns an class from an input string in the format of an import
 * class_factory - generates an instance of a class from strings (including multiple 
   inheritance) with input attribute data supply if required

.. code-block:: python

    from bom_analysis.utils import class_factory, class_from_strings

    Assembly = class_from_strings("bom_analysis.Assembly")
    bolt_and_nut = Assembly(ref="bolt_and_nut")

    nut = class_factory("Component", ["bom_analysis.Component"], dict(ref="hex_nut"))

See the :obj:`bom_analysis.utils.class_factory` for docstrings.

-----------------------------
A Global Configuration
-----------------------------

A global configuration file is in Bill of Materials analysis which contains
defaults for the definition of the BOM.

Having a configuration that can be shared across all analysis
ran on the bill of materials is key to running complex workflows.
The configuration could include features of the Bill of Materials
such as being able to dynamically add new parameters or information
for analysis tools such as working directory or login details.

Bill of Materials Analysis features such a class that can be imported
without initialisation and with data shared using it.

The information about using a configuration can be found :ref:`here <configure analysis>`.