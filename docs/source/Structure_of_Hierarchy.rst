======================
Structure of Hierarchy
======================
In Nuclear Fusion, the tokamak is an extremely complex system that requires significant multiphysics analysis
of varying levels of fidelity in the design process. The core concept of creating of a bill of materials and 
then utilising it for analysis stems from the desire to have a structure to analytical data that can be more 
easily understood.

A bill of materials can be made up of various objects that link together into a hierarchical structure that
represents the system. These object can then have data assigned to them that can be accessed/used - for example 
a low fidelity analysis may assign a single temperature to a component and a higher fidelity analysis may assign 
a complex profile, either way access to this data (and the related component) is clear to a user.

`A worked example of using the Hierarchy can be found here <https://git.ccfe.ac.uk/step/invesselcomponents/outboardblanket/bom_analysis/-/blob/development/examples/example_0%20-%20Defining%20a%20Bill%20of%20Materials.ipynb>`__

----------------------------
Component - The Lowest Level
----------------------------

.. automodule:: bom_analysis.Component

Defining a component is simple with the reference (such as a part number) supplied as an optional input.

.. code-block:: python

    bolt = Component(ref="P10154")
    nut = Component(ref="P50501")
    flange = Component(ref="P09876")

See the :obj:`bom_analysis.bom.Component` for docstrings.

The ref key word is a unique reference (such as a part number) and is a key concept covered in more detail :ref:`here <reference concept>`.


-----------------------------------------------
Assembly - Made of of Components and Assemblies
-----------------------------------------------
.. automodule:: bom_analysis.Assembly

.. code-block:: python

    bolt_and_nut = Assembly(ref="P12345")
    flange_assembly = Assembly(ref="P00000")
    bolt_and_nut.add_components([bolt, nut])
    flange_assembly.add_components([flange, bolt_and_nut, bolt_and_nut, bolt_and_nut])

See the :obj:`bom_analysis.bom.Assembly` for docstrings.

--------------------------------------------------
Homogenised Assembly - An Assembly with a Material
--------------------------------------------------
.. automodule:: bom_analysis.HomogenisedAssembly

See the :obj:`bom_analysis.bom.HomogenisedAssembly` for docstrings.

------------------------------------------------
Reference - The Most Important Thing to Remember
------------------------------------------------
.. _reference concept:

.. automodule:: bom_analysis.bom.EngineeringObject.ref


See the :obj:`bom_analysis.bom.EngineeringObject.ref` for docstrings.

--------------------------------------------
Flattening Hierarchy - Making Things Easier
--------------------------------------------
The bill of materials can be flattened and returned as a dictionary. This is useful
when operating on all objects in the hierarchy.

.. code-block:: python

    bolt_and_nut.add_component(nut)

    flatbolt_and_nut.flatten()

    >> {"P12345":bolt_and_nut, "P10154":bolt, "P50501":nut}

See the :obj:`bom_analysis.bom.Assembly.flatten` for docstrings.