====================
Variables
====================

The bill of materials can contain a lot of information that is required 
by for analyses and there are a number of ways to access that information.

`Examples notebook showing of using deifferent variables is here  <https://github.com/ukaea/bom_analysis/blob/main/examples/example_0%20-%20Defining%20a%20Bill%20of%20Materials.ipynb>`__


--------------------
Parameters
--------------------

.. automodule:: bom_analysis.parameters.ParameterFrame
                :noindex:

.. code-block:: python

    from bom_analysis import Q_
    bolt.params.mass = Q_(0.1, "kg")   
    print(bolt.params.mass.to("g"))
    >> "100 g"

See the :obj:`bom_analysis.parameters.ParameterFrame` for docstrings.

--------------------
Assignment
--------------------

.. automodule:: bom_analysis.bom.EngineeringObject.assignment
                :noindex:

.. code-block:: python

    bolt.assignment = "buttress thread"
    bolt.assignment = "subsea yellow"
    print(bolt.assignment)
    >> np.array(["buttress thread", "subsea yellow"])    

See the :obj:`bom_analysis.bom.EngineeringObject.Assignment` for docstrings.

-------------------
Counting Parts
-------------------
Multiples of the same part can be added to the bill of materials.

.. code-block:: python

    bolt_and_nut.add_component(nut)

    bolt_and_nut.part_count("hex_nut")
    >> 2

This will return and integer of 2 as there are 2 hex nuts in the assembly.

See the :obj:`bom_analysis.bom.Assembly.part_count` for docstrings.

--------------------
Looking Up Variables
--------------------
Variables can be extracted from the bill of materials parameters or any other attributes.
All variable in all subcomponents of an assembly (and there subcomponents, to the lowest)
will be extracted and a dictionary returned.

.. code-block:: python

    bolt_and_nut.lookup("material")
    bolt_and_nut.lookup_params("mass")
    >> {"P12345":{"mass":Q_(0.1, "kg")}}

See the :obj:`bom_analysis.bom.Assembly.lookup_params` for docstrings.

--------------------
Accessing Nested
--------------------
As a lot of BOM analysis can work with dictionaries, a function was included that allows
extraction of a value from a heavily nested dictionary.

.. code-block:: python

    from bom_analysis.utils import access_nested
    example = {"a":{"b"{"c"{"d":"e"}}}}
    access_nested(example, ["a", "b", "c", "d"])
    >> "e"

See the :obj:`bom_analysis.utils.access_nested` for docstrings.

--------------------
Wrapped Dataframe
--------------------

.. automodule:: bom_analysis.base.DFClass
                :noindex:

See the :obj:`bom_analysis.base.DFClass` for docstrings.