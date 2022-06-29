====================
Materials
====================

Given that it is a bill of materials structure, all Components (and HomogenisedAssembly)
have a materials object which can allow for data extraction.

`A worked example of using the Hierarchy can be found here <https://git.ccfe.ac.uk/step/invesselcomponents/outboardblanket/bom_analysis/-/blob/development/examples/example_4%20-%20Handling%20Materials.ipynb>`__

--------------------
Materials Object
--------------------
.. automodule:: bom_analysis.materials.MaterialData

See the :obj:`bom_analysis.materials.MaterialData` for docstrings.

--------------------
Selecting Materials
--------------------
.. automodule:: bom_analysis.utils.MaterialSelector

See the :obj:`bom_analysis.utils.MaterialSelector` for docstrings.

--------------------
Translating
--------------------
.. automodule:: bom_analysis.utils.Translator

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