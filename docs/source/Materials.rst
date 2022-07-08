====================
Materials
====================

Given that it is a bill of materials structure, all Components (and HomogenisedAssembly)
have a materials object which can allow for data extraction.

`A worked example of using the Hierarchy can be found here <https://github.com/ukaea/bom_analysis/blob/main/examples/example_4%20-%20Handling%20Materials.ipynb>`__

--------------------
Materials Object
--------------------
A parent material data class MaterialData is provided in BOM Analysis
(alongside CoolProp and DataFrame children). The MaterialData class is added
by default to Components and Homogenised Assemblies in the BOM.

The materials have four key properties:
    * mat - the name of the material
    * temperature - the temperature of the material
    * pressure - the pressure of the material
    * irradiation - the Displacement per Atom of the material

These four properties can be supplied to a data source to
extract material data at the input values using the extract_property
method. The material also has a feature to check whether a material
exists in the database - to do this successfully it is likely
that the translation class is utilised as different databases tend
to use different naming formats.

Additional, the material classes have the data_warpper method which
calls the extract_property for the instance with the benefit that
if the property (or material) does not exist in the database of that
instance it will check the other databases within the MaterialSelector.

See the :obj:`bom_analysis.materials.MaterialData` for docstrings.

--------------------
Selecting Materials
--------------------
The MaterialSelector can select a material database based on a priority order
and the availability of the material within the database. To perform this function
the material selector should be supplied with the databases (generally children of the
MaterialData class).

To add the databases to the material selector the add_database method can be used with
the add order assumed to be the priority.

If the selector was provided a ASME materials database followed by a CoolProp database
followed by a in-house database during setup, then the material for a component can
be returned by the select_database method. Say the material is Beryllium, the MaterialSelector
will check the ASME database, then the CoolProps, then the in-house until it finds (or not)
Beryllium.

One of the benefits of using MaterialSelector (and storing it in the Configuration) is that
when a material is not within one database the next can be checked as discussed in the MaterialData.

See the :obj:`bom_analysis.utils.MaterialSelector` for docstrings.

--------------------
Translating
--------------------
Translating strings can be very important to a bill of materials
and a workflow due to mismatches in the naming is common across
material libraries (both the name and the parameters).

The translator can be defined from a dictionary and utilises classmethods
so can be used without initialisation. After the underlying data has been
populated, the input for translation can be supplied alongside the output format.

.. code-block:: python

    from bom_analysis.utils import Translator
    translated_str = Translator("input string", "output for string")

See the :obj:`bom_analysis.utils.Translator` for docstrings.

---------------------
Material Data Wrapper
---------------------
The material data wrapper is used to exact material data
from a Material using the extract_property method. The 
additonal benefor of using data_wrapper is that it will
check all the other material libraries in the MaterialSelector
within the Configuration if it cannot find it within 
the data of that material class.

See the :obj:`bom_analysis.materials.MaterialData.data_wrapper` for docstrings.