
------------
Installation
------------

The easiest way to install bom_analysis is using pip ``pip``::

    pip install bom_analysis



-------
Testing
-------

BOM Analysis contains a test suite that can be ran using pytest (must be installed). Three markers have been used to distiguish the different testing levels:
- unittest: runs unit tests that generally only test an individual method by using mocking
- integrationtest: runs the integration tests
- regressiontest: tests bugs that have been indentified in other versions

The full test suite can be ran by navigating to the source directory and running ``pytest``::

    pytest 

It is possible to filter the tests by the markers::

    pytest -m "unittest"

Or filter out markers::

    pytest -m "not integrationtest and not regressiontest"