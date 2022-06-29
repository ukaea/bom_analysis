import setuptools

setuptools.setup(
    name="bom_analysis",
    version="1.0.0",
    description="Bill of Materials for Analysis",
    author="UK Atomic Energy Authority",
    maintainer="Sam Merriman",
    maintainer_email="samuel.merriman@ukaea.uk",
    url="https://git.ccfe.ac.uk/step/invesselcomponents/outboardblanket/bom_analysis",
    packages=["bom_analysis"],
    install_requires=[
        "numpy",
        "pint",
        "pandas",
        "tabulate",
        "CoolProp",
        "fluids",
        "treelib",
        "python-box",
    ],
    python_requires=">=3.6",
    license="BSD 3-Clause “New” or “Revised” License",
    classifiers=["License :: OSI Approved :: BSD License"],
)
