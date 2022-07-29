[![Documentation Status](https://readthedocs.org/projects/bom-analysis/badge/?version=latest)](https://bom-analysis.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ukaea_bom_analysis&metric=coverage)](https://sonarcloud.io/summary/new_code?id=ukaea_bom_analysis)

[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=ukaea_bom_analysis)](https://sonarcloud.io/summary/new_code?id=ukaea_bom_analysis)


# Bill of Materials Analysis

This repository allows for an engineering assembly to be represented in a Bill of Materials 
(BOM) structure for analysis. The aim was to reduce the cognative complexity of the various data
sets that are required for input or output of an analysis workflow. The repository also
includes a number of features to help with this analysis.

The motivation for this package comes from a desire to order complex
system data used by analysis in a logical. The chosen method
for ordering this data is the bill of materials as it provides a common
framework used across engineering.

The bill of materials provides a hieracy of materials, components, and assemblies
all of which can contain data that is important for the analysis. For example,
a user may want to assess the mass of an assembly by summing the mass of all
the components in that make it up.

The Bill of Materials can be plotted to help understand the system (taken from [example](https://github.com/ukaea/bom_analysis/blob/main/examples/example_1%20-%20Loading_a_Bill_of_Materials.ipynb)):

    tokamak
    ├── coil_set
    │   ├── east
    │   ├── north
    │   ├── south
    │   └── west
    └── divertor

The data for each of the components can also be displayed easily:

    ================================================================================
    | var           │ value   │ unit          │ description                        │
    ================================================================================
    │ mass          │ 1000    │ metric_ton    │                                    │
    ================================================================================
    │ configuration │ ST      │ dimensionless │                                    │
    ================================================================================
    │ major_radius  │ 2       │ meter         │ the geometric centre of the plasma │
    ================================================================================    

## Installation

The easiest way to install bom_analysis is using pip ``pip``:

    pip install bom_analysis


## Help and Support

- [Documentation](https://bom-analysis.readthedocs.io/en/latest/index.html#)

- [Example on Defining a Bill of Material](https://github.com/ukaea/bom_analysis/blob/main/examples/example_0%20-%20Defining%20a%20Bill%20of%20Materials.ipynb)

- [Example on Loading a Bill of Material](https://github.com/ukaea/bom_analysis/blob/main/examples/example_1%20-%20Loading_a_Bill_of_Materials.ipynb)

- [Example on Creating a Skeleton](https://github.com/ukaea/bom_analysis/blob/main/examples/example_2%20-%20Creating%20a%20Skeleton%20from%20Scratch.ipynb)

- [Example on Useful Features](https://github.com/ukaea/bom_analysis/blob/main/examples/example_3%20-%20Other%20Useful%20Classes.ipynb)

- [Example on Handling Materials](https://github.com/ukaea/bom_analysis/blob/main/examples/example_4%20-%20Handling%20Materials.ipynb)


## Testing

BOM Analysis contains a test suite that can be ran using pytest (must be installed). Three markers have been used to distiguish the different testing levels:
- unittest: runs unit tests that generally only test an individual method by using mocking
- integrationtest: runs the integration tests
- regressiontest: tests bugs that have been indentified in other versions

The full test suite can be ran by navigating to the source directory and running ``pytest``:

    pytest 

It is possible to filter the tests by the markers:

    pytest -m "unittest"

Or filter out markers:

    pytest -m "not integrationtest and not regressiontest"

## License
[BSD 3](LICENSE)
