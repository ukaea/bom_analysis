.. Bill of Materials Analysis documentation master file, created by
   sphinx-quickstart on Sat May  8 08:10:27 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bill of Materials Analysis's documentation!
======================================================

This repository allows for an engineering assembly to be represented in a Bill of Materials 
(BOM) structure for analysis. The aim was to reduce the cognative complexity of the various data
sets that are required for input or output of an analysis workflow. The repository also
includes a number of features to help with this analysis.

The documentation aims to introduce the bill of materials in sections, then groups
concepts and functions around how a user can utilise this Bill of Materials analysis in
their work.

The motivation for this package comes from a desire to order complex
system data used by analysis in a logical. The chosen method
for ordering this data is the bill of materials as it provides a common
framework used across engineering.

The bill of materials provides a hieracy of materials, components, and assemblies
all of which can contain data that is important for the analysis. For example,
a user may want to assess the mass of an assembly by summing the mass of all
the components in that make it up.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   Installation_and_Testing.rst
   Structure_of_Hierarchy.rst
   Defining_a_Bill_of_Materials.rst
   Variables.rst
   Materials.rst
   Analysis.rst
   bom_analysis.rst
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
