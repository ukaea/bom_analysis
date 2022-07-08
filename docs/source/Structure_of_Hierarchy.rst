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

`A worked example of using the Hierarchy can be found here <https://github.com/ukaea/bom_analysis/blob/main/examples/example_0%20-%20Defining%20a%20Bill%20of%20Materials.ipynb>`__

----------------------------
Component - The Lowest Level
----------------------------

The component is the lowest level Engineering Object in the Bill of
Materials and, critically has a material assigned to it.

A Component can generally be considered a physical object made up of a
single material, for example a bolt made of high strength steel.

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
An assembly can be made up of multiple sub components which
assemble together to form the assembly. The assembly does not have
a material assigned to it as it will contain the multiple materials
of the components.

An assembly can generally be considered to be made up of multiple
other assemblies/components, for example a nut and bolt assembly
or an assembly of nut and bolt assemblies with a flange component.

.. code-block:: python

    bolt_and_nut = Assembly(ref="P12345")
    flange_assembly = Assembly(ref="P00000")
    bolt_and_nut.add_components([bolt, nut])
    flange_assembly.add_components([flange, bolt_and_nut, bolt_and_nut, bolt_and_nut])

See the :obj:`bom_analysis.bom.Assembly` for docstrings.

--------------------------------------------------
Homogenised Assembly - An Assembly with a Material
--------------------------------------------------
A homogenised assembly is a special type of assembly
which does not exist in the physical world but instead
is analytical (particularly for neutronics analysis). A
Homogenised assembly can have both sub components and
materials assigned to it.

An example of the analytical use of a Homogenised assembly
would be a bolt and nut assembly represented as a single
body in structural FEA to simplifly the analysis.

See the :obj:`bom_analysis.bom.HomogenisedAssembly` for docstrings.

------------------------------------------------
Reference - The Most Important Thing to Remember
------------------------------------------------
.. _reference concept:

A reference which represents a unique variable for an engineering component
such as a part number. The reference can be any string, the key is that it is
unique to the part. Multiple assemblies within a system can have the same reference
within them but the Engineering Object with this reference in *all* assemblies
must be the same.

For example, a bolt made of Carbon Steel and a bolt made up of Stainless Steel
may have exactly the same dimensions and in the same system on different assemblies
must not have the same reference because the object is not the same.

Practically, a hierarchy has a master register of references with weakref to the
object. When assemblies are added to one another, or a component is added to an
assembly at any level in the hierarchy, the master register is consulted and
checked to ensure that the reference has not been used on another part. The
reference is a property of all Engineering Objects.


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