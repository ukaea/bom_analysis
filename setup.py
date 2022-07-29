import setuptools

setuptools.setup(
    name="bom_analysis",
    version="1.0.0",
    description="A framework for performing analysis based on a Bill of Materials (BOM) structure",
    long_description=open('README.txt').read(),
    long_description_content_type="text/markdown",
    author="UK Atomic Energy Authority",
    maintainer="Sam Merriman",
    maintainer_email="samuel.merriman@hotmail.co.uk",
    url="https://github.com/ukaea/bom_analysis",
    packages=["bom_analysis"],
    install_requires=[
        "numpy",
        "pint",
        "pandas",
        "tabulate",
        "CoolProp",
        "treelib",
        "python-box",
        "pre-commit",
    ],
    python_requires=">=3.6",
    license="BSD 3-Clause “New” or “Revised” License",
    classifiers=["License :: OSI Approved :: BSD License"],
)
