===============================
Defining a Bill of Materials
===============================

The definition of a bill of materials is required and can be done manually
by assembling components and assemblies, by parsing together a set of .json/dictionary, 
or by loading in a previous BOM from a skeleton.

-------------------
The Skeleton
-------------------

.. automodule:: bom_analysis.base.BaseClass
                :noindex:

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
.. automodule:: bom_analysis.parsers.SkeletonParser
                :noindex:

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

.. automodule:: bom_analysis.base.BaseConfig
                :noindex:

The information about using a configuration can be found :ref:`here <configure analysis>`.
