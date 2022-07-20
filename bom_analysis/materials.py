from functools import wraps
from gettext import translation
from pathlib import Path
from typing import Callable, Optional, Union

import CoolProp.CoolProp as cp
import pandas as pd
from pint import Quantity

from bom_analysis import ureg, run_log, Q_
from bom_analysis.base import BaseClass, BaseFramework
from bom_analysis.utils import Translator

COOLPROPUNITS: dict = dict(
    T="K",
    P="Pa",
    D="kg/m**3",
    C="J/kg/K",
    O="J/kg/K",
    U="J/kg",
    H="J/kg",
    S="J/kg/K",
    A="m/s",
    G="J/kg",
    V="Pa*s",
    L="W/m/K",
    conductivity="W/m/K",
    viscosity="Pa*s",
)


class NoMaterialDataException(Exception):
    pass


class MaterialPropertyDoesNotExistError(Exception):
    pass


def exception_handler(func: Callable) -> Callable:
    """
    A custom descriptor that returns an error when a function
    fails.

    This raises a NoMaterialDataException when the the method
    which is wrapped fails.

    Parameters
    ----------
    func : Callable
        The function wrapped by the descriptor.

    Returns
    -------
    Callable
        The wrapper for the function.

    Raises
    ------
    NoMaterialDataException
        if the method has failed.

    Note
    ----
    Information about creating an exception handler can be found here:
    https://medium.com/swlh/handling-exceptions-in-python-a-cleaner-way-using-decorators-fae22aa0abec"""

    @wraps(func)
    def wrapper(*args):
        try:
            result = func(*args)
        except BaseException as e:
            raise NoMaterialDataException from e
        return result

    return wrapper


class MaterialData(BaseClass):
    """A parent material data class MaterialData is provided in BOM Analysis
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
    instance it will check the other databases within the MaterialSelector."""

    to = ""

    def __init__(
        self,
        mat: Optional[str] = None,
        temperature: Quantity = Q_(293.0, "K"),
        pressure: Quantity = Q_(100000.0, "Pa"),
        irradiation: Quantity = Q_(0.0, "dpa"),
        **kwargs,
    ):
        """Initialises the materials data.

        Parameters
        ----------
        mat : str, optional
            A string contianing the material name.
        temp : pint instance, optional
            The temperature of the material.
        pressure : pint instance, optional
            The pressure of the material.
        irradiation : Pint, optional
            The irradiation damage in DPA.
        kwargs : tuple
            Key word arguments just for legacy naming.
        """
        if "temp" in kwargs:
            temperature = kwargs["temp"]
        self._mat = None
        self._pressure = None
        self._temperature = None
        self._irradiation = None

        self.temperature = temperature
        self.pressure = pressure
        self.irradiation = irradiation
        self.mat = mat

    def __repr__(self) -> str:
        """Print of the material inputs.

        Returns
        -------
        str
            A string for printing."""
        string = f"Material = {self.mat}\n\n"
        string += f"temperature = {self.temperature}\npressure = {self.pressure}\n"
        return string

    @property
    def mat(self) -> Optional[str]:
        """The name of the material.

        Returns
        -------
        str
            The name of the material.
        """
        return self._mat

    @mat.setter
    def mat(self, value: str):
        """The setter for the material of the
        component.

        Parameters
        ----------
        value : str
            The material to be assigned.
        """
        self._mat = value

    @property
    def pressure(self) -> Quantity:
        """The pressure of the material.

        Returns
        -------
        Quantity
            The pressure of the material.
        """
        return self._pressure

    @pressure.setter
    def pressure(self, value: Quantity):
        """The setter for the pressure of the
        component.

        Parameters
        ----------
        value : Quantity
            The pressure value to be assigned.
        """
        self._pressure = value

    @property
    def temperature(self) -> Quantity:
        """The temperature of the material.

        Returns
        -------
        Quantity
            The temperature of the material.
        """
        return self._temperature

    @temperature.setter
    def temperature(self, value: Quantity):
        """The setter for the temperature of the
        component.

        Parameters
        ----------
        value : Quantity
            The temperature value to be assigned.
        """
        self._temperature = value

    @property
    def irradiation(self) -> Quantity:
        """The irradiation of the material.

        Returns
        -------
        The irradiation of the material.
        """
        return self._irradiation

    @irradiation.setter
    def irradiation(self, value: Quantity):
        """The setter for the irradiation of the
        component.

        Parameters
        ----------
        value : Quantity
            The irradiation value to be assigned.
        """
        self._irradiation = value

    def from_dict(self, data: dict):
        """Imports from a json and populates the material.

        Parameters
        ----------
        data : dict
            A dictionary containing the material data."""
        super().from_dict(data)
        if "_mat" in data:
            self.mat = data["_mat"]
        elif "name" in data:
            self.mat = data["name"]
        else:
            run_log.warning(f"no material name given for {self}")

    @property
    def reftemp(self) -> Quantity:
        """Reftemp is legacy to fit with
        some older external codes.

        Returns
        -------
        The temperature of the material.
        """
        return self._temperature

    @reftemp.setter
    def reftemp(self, value: Quantity):
        """Reftemp is legacy to fit with
        some older external codes.

        Parameters
        ----------
        value : Quantity
            The temperature value to be assigned.
        """
        self._temperature = value

    def add_defaults(self, data: dict):
        self.from_dict(data)

    def SetRefTemp(self, Temp: Quantity = Q_(293.0, "K")):
        """Sets the component temperature.

        Parameters
        ----------
        Temp : pint instance, optional
            A pint instance for the component temperature.

        Note
        ----
        This naming and function was based on a now
        depricated material property in an external
        library."""
        run_log.warning("using legacy methods in material assignment")
        self.temperature = Temp

    def SetRefPressure(self, pressure: Quantity = Q_(100000.0, "Pa")):
        """Sets the component pressure.

        Parameters
        ----------
        pressure : pint instance, optional
            A pint instance for the component pressure.

        Note
        ----
        This naming and function was based on a now
        depricated material property in the external
        library analysislib."""
        run_log.warning("using legacy methods in material assignment")
        self.pressure = pressure

    def SetLibMaterial(self, mat: str):
        """Sets the material name under the private
        material variable _mat.

        Parameters
        ----------
        mat : str
            A string of the material name.

        Note
        ----
        This naming and function was based on a now
        depricated material property in the external
        library."""
        run_log.warning("using legacy methods in material assignment")
        self.mat = mat  # Material from library

    @staticmethod
    def check(mat: str, **kwargs) -> bool:
        """Checks a library for a material, not implemented
        within the parent class.

        Raises
        ------
        NotImplementedError
            Not implemented within the parent class."""
        raise NotImplementedError()

    def extract_property(self, property_name: str):
        """Extracts a property from the MaterialData, not
        implemented in the parent class.

        Parameters
        ----------
        property_name : str
            The property to be extracted from the material data.

        Raises
        ------
        NotImplementedError
            Not implemented in the parent class.
        """
        raise NotImplementedError()

    def data_wrapper(
        self, property_name: str, i_database: int = 0
    ) -> Union[Quantity, float]:
        """Wraps the material data from the MaterailData
        extract property with a try except.

        The except is raised if a NoMaterialDataExtraction
        is raised (i.e. if a material property cannot be
        extracted from this class). If this exception is raised
        the method will attempt to extract the property
        from the next class in the MaterialSelector.priority_order.
        The MaterialSelector is in the
        framework.base.BaseFramework._configuration.materials.

        Parameters
        ----------
        property_name : str
            The name of the property which will be extracted.
        i_database : int, optional
            The integer which calls the material class in the
            MaterialSelector.priority_order , by default 0.

        Returns
        -------
        Q_, float
            The extracted material property at the pressure and
            temperature of the material.

        Raises
        ------
        MaterialPropertyDoesNotExistError
            If the material property does not exist in any of the
            classes in the MaterialSelector.priority_order.
        """
        try:
            output = self.extract_property(property_name)
        except NoMaterialDataException:
            run_log.warning(
                f"{Translator(self.mat, self.to)} {Translator(property_name, self.to)} not in {str(type(self))}"
            )
            material_selector = BaseFramework._configuration.materials
            if len(material_selector.priority_order) - 1 < i_database:
                raise MaterialPropertyDoesNotExistError(
                    f"cannot find {property_name} for {self.mat}"
                )

            database = material_selector.priority_order[i_database]
            new_material = material_selector.intialised_database(self.mat, database)
            new_material.pressure = self.pressure
            new_material.temperature = self.temperature
            new_material.irradiation = self.irradiation

            output = new_material.data_wrapper(property_name, i_database=i_database + 1)

        return output


class DFLibraryWrap(MaterialData):
    """A material data which pulls from a DataFrame."""

    def __init__(
        self,
        mat: Union[str, None] = None,
        temperature: Quantity = Q_(293.0, "K"),
        pressure: Quantity = Q_(100000.0, "Pa"),
        **kwargs,
    ):
        """A dataframe material library which extracts a
        material property from a datataframe.

        Parameters
        ----------
        mat : str, optional
            The material name, by default None.
        temperature : Quantity, optional
            The temperature of the material, by default Q_(293.0, "K").
        pressure : Quantity, optional
            The pressure of the material, by default Q_(100000.0, "Pa").

        Attributes
        ----------
        _mat_data : pd.DataFrame
            The material data.
        path : str
            The path to a .json which the DataFrame can be loaded form.
        to : str
            A string which defines the output of translator.
        """
        super().__init__(mat=mat, temperature=temperature, pressure=pressure)
        self._mat_data = pd.DataFrame()
        self.path = None
        self.to = ""

    @staticmethod
    def check(mat: str, **kwargs) -> bool:
        """Checks the underlying dataframe for a material
        name.

        The material name can be supplied alongside a
        translate_to key word argument to allow the name to
        be translated into a particular form.

        Parameters
        ----------
        kwargs : key word arguements
            Supplied keyword arguments.

        Returns
        -------
        bool
            A True/False on whether the material exists in the library.

        Note
        ----
        Translate_to must be supplied therefore this should
        be reflected format of the method."""
        if "translate_to" in kwargs:
            to = kwargs["translate_to"]
        else:
            to = None
        if "path" in kwargs:
            data = pd.read_json(Path(kwargs["path"]))
        else:
            raise ValueError("dataframe database must be suplied a path")
        translation = Translator(mat, to)
        if translation in data.columns:
            return True
        else:
            return False

    def from_dict(self, data: dict):
        """Imports from a json and populates the material.

        Runs the parent class then uses the dataframe read_json
        method.

        Parameters
        ----------
        data : dict
            A dictionary containing the material data.

        See Also
        --------
        pandas.DataFrame.read_json : The method for reading a json."""
        super().from_dict(data)
        self._mat_data = pd.read_json(data["path"])

    def to_dict(self, exclusions=["_mat_data"]) -> dict:
        """
        Exports the data for storage in a json file.

        Runs the to_dict method excluding the material
        data.

        See Also
        --------
        base.BaseClass.to_dict : Parent to_dict.
        """
        return super().to_dict(exclusions=exclusions)

    @exception_handler
    def extract_property(self, property_name: str) -> Union[Quantity, float]:
        """Primary method for extracting data from the
        materials database.

        Parameters
        ----------
        property_name : str
            The name of the proprty to be extracted from the
            material data.

        Returns
        -------
        Union[Quantity, float]
            The output of the material data for the property name."""
        run_log.warning("no calculated material data dependancy")

        if self._mat_data.empty and self.path is not None:
            self._mat_data = pd.read_json(Path(self.path))

        output = self._mat_data.at[
            Translator(property_name, self.to), Translator(self._mat, self.to)
        ]

        if "units" in self._mat_data.columns.values:
            unit = self._mat_data.at[Translator(property_name, self.to), "units"]
        else:
            unit = None
        if output is not None:
            output = float(output) * ureg(unit)
        return output

    def __repr__(self) -> str:
        """Print of where the material data came from.

        Returns
        -------
        str
            A string for printing."""
        string = super().__repr__()
        string += "data from DataFrame dictionary"
        return string


class CoolPropsWrap(MaterialData):
    """A wrapper for CoolProps with pint units.

    Attributes
    ----------
    to : str
        The string argument that will be used
        by the translator.
    """

    to = "CoolProps"

    @staticmethod
    def check(mat: str, **kwargs) -> bool:
        """Checks CoolProps for a material
        name.

        The material name can be supplied alongside a
        translate_to key word argument to allow the name to
        be translated into a particular form.

        Parameters
        ----------
        kwargs : key word arguements
            Supplied keyword arguments.

        Returns
        -------
        bool
            A True/False on whether the material exists in the library.

        See Also
        --------
        CoolProp : Coolant material data.

        Note
        ----
        Translate_to must be supplied therefore this should
        be reflected format of the method."""
        if "translate_to" in kwargs:
            to = kwargs["translate_to"]
        else:
            to = "CoolProps"
        translation = Translator(mat, to)
        if translation in cp.get_global_param_string("FluidsList"):
            return True
        else:
            return False

    @exception_handler
    def extract_property(self, property_name: str) -> Quantity:
        """Extracts a property from CoolProp and returns
        the quivalent Pint Quantity.

        Uses the global parameter COOLPROPUNITS to define
        the units (the test suite will fail if later versions
        of coolprops change this). Only outputs properties
        by that need pressure and temperature inputs and not
        properties that need other inputs such as surface
        tension. Will translate a property_name into the
        CoolProp format if included in the translator.

        Parameters
        ----------
        property_name : str
            The string of the property to be used by CoolProp
            or to be translated into the string used by CoolProp.

        Returns
        -------
        Q_
            Quantity for the property at the material temperature
            and pressure.
        """
        coolprops_output = Translator(property_name, self.to)
        value = cp.PropsSI(
            coolprops_output,
            "P",
            self.pressure.to("Pa").magnitude,
            "T",
            self.temperature.to("K").magnitude,
            Translator(self.mat, self.to),
        )
        unit = COOLPROPUNITS[coolprops_output]
        return Q_(value, unit)

    def __repr__(self) -> str:
        """Print of where the material data came from.

        Returns
        -------
        str
            A string for printing."""
        string = super().__repr__()
        string += "data from CoolProps"
        return string


class Composition(MaterialData):
    """A homogenised material composition."""


class Solid(MaterialData):
    """The material object
    may want to bring the tritium and temperature information within."""


class Fluid(MaterialData):
    """
    A class defining a fluid material wrapping a generic material from
    the library with fluid specific ease of use property access.
    """
