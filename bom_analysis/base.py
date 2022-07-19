from builtins import getattr, hasattr
import types
from pathlib import Path
import os
import textwrap
from getpass import getpass
from typing import Union, Any, Callable, Optional, Dict

import json
import numpy as np
import pandas as pd
from tabulate import tabulate

from bom_analysis import run_log, Q_
from bom_analysis.utils import (
    Translator,
    UpdateDict,
    encoder,
    decoder,
    MaterialSelector,
    change_handler,
)


class ConfigurationNotFullyPopulated(Exception):
    """An exception for when the configuration is not
    populated correctly with all the information required
    for a method to function correctly.
    """

    pass


def add_base_class(
    existing_object: Any,
    import_method: Callable[[Any], Any],
    export_method: Callable[[Any], Any],
):
    """Adds an import and export function to a class under the
    name export_data and import_data.

    This is currently unused and maybe should be removed.
    The original intention was to be able to add methods
    to allow json compatible output dictionaries to
    external functions.

    Parameters
    ----------
    existing_object : Any
        data for which the methods will be added to.
    import_method : function
        the import method.
    export_method : function
        the export method.

    Note
    ----
    Information on add a mehtod to an instance:
    https://stackoverflow.com/questions/972/adding-a-method-to-an-existing-object-instance"""
    existing_object.export_data = types.MethodType(export_method, existing_object)
    existing_object.import_data = types.MethodType(import_method, existing_object)


class MetaConfig(type):
    """
    The Meta class which defines properies and setters
    that can be used on the configuration without initialising it and our shared
    like class properties.

    Including properties and setters allows for better error handling and defaulting
    of values. If a calculation is performed that called a translation but the
    translator has not been defined within the configuration then a specific error
    will be raised. If a plot directory is called then but it has not been defined
    then it will default to the working directory.
    """
    _materials : MaterialSelector

    @property
    def materials(cls) -> MaterialSelector:
        """The property for the materials data.

        Returns
        -------
        _materials
            The priority order and location of the materials.

        Raises
        ------
        ConfigurationNotFullyPopulated
            Error if the private variable populated with None.
        """
        selector : MaterialSelector = cls._materials
        return selector

    @materials.setter
    def materials(cls, value: Union[dict, MaterialSelector]):
        """Setter for the materials.

        Parameters
        ----------
        value : dict
            Material data to be assigned.

        Raises
        ------
        TypeError
            If the value is not a dictionary or
            a material selector.
        """
        if isinstance(value, dict):
            cls._materials.from_dict(value)
        elif isinstance(value, MaterialSelector):
            cls._materials = value
        else:
            msg = "materials must be MaterialSelector instance or dict"
            run_log.error(msg)
            raise TypeError(msg)

    @property
    def restrict_param(cls):
        """Boolean whether the parameters can
        be edited on the fly.

        Locking down parameters so that they have
        to be predefined offers some advantages as
        it prevents a mash up of spelling mistakes
        and poorly thought out parameters. It does,
        however, reduce ease of use.
        """
        return cls._restrict_param

    @restrict_param.setter
    def restrict_param(cls, value: bool):
        """Setter for parameter restriction

        Parameters
        ----------
        value : bool
            Boolean for whether or not parameters should be restricted.
        """
        cls._restrict_param = value

    @property
    def parameters(cls) -> list:
        """A property for the location of any parameter files that
        can be used to build the skeleton of the bill of materials.

        Returns
        -------
        list
            A list of locations of the .json that make up the paramaters
            to be assembled into the skeleton.

        Raises
        ------
        ConfigurationNotFullyPopulated
            If the property is called but the configuration
            has not been populated and has the property is None.
        """
        if cls._parameters is None:
            msg = (
                "location of any files which contain json parameters "
                "to be assembled required as a list of strings"
            )
            run_log.error(msg)
            raise ConfigurationNotFullyPopulated(msg)
        return cls._parameters

    @parameters.setter
    def parameters(cls, value: list):
        cls._parameters = value

    @property
    def translations(cls) -> list:
        """A property for the locations of the .json that will
        be loaded into the transaltor.

        Returns
        -------
        list
            Location of translation file.

        Raises
        ------
        ConfigurationNotFullyPopulated
            If the property is called but the configuration
            has not been populated and has the property is None.
        """
        if cls._translations is None:
            msg = (
                "translation location not defined, the file location"
                "required as a list of strings"
            )
            run_log.error(msg)
            raise ConfigurationNotFullyPopulated(msg)
        return cls._translations

    @translations.setter
    def translations(cls, value: list):
        cls._translations = value
        Translator.define_translations(cls.translations)

    @property
    def parts(cls) -> list:
        """The parts section of the configuration are
        used by the parsers to contain information about
        parts to be parsed to form the skeleton (dictionary form) of a
        Bill of Materials.

        Returns
        -------
        list
            The object assigned to parts.

        Raises
        ------
        ConfigurationNotFullyPopulated
            If the property is called but the configuration
            has not been populated and has the property is None.
        """
        if cls._parts is None:
            msg = (
                "location of any files which contain json parts"
                " to be assembled required as a list of strings"
            )
            run_log.error(msg)
            raise ConfigurationNotFullyPopulated(msg)
        return cls._parts

    @parts.setter
    def parts(cls, value: list):
        cls._parts = value

    @property
    def working_dir(cls) -> str:
        """The working directory for the Configuration.

        Returns
        -------
        str
            Path to working directory.
        """
        return cls._working_dir

    @working_dir.setter
    def working_dir(cls, value: str):
        cls._working_dir = value

    @property
    def default_param_type(cls) -> str:
        """The default parameter type that
        will be assigned to all components and
        assemblies attribute params.

        Returns
        -------
        str
            String path to the param type.
        """
        return cls._default_param_type

    @default_param_type.setter
    def default_param_type(cls, value: str):
        cls._default_param_type = value

    @property
    def temp_dir(cls) -> Union[str, Path]:
        """The temporary directory for outputs.

        Returns
        -------
        str
            Path to the temporary directory.
        """
        if cls._temp_dir is None:
            msg = "temp_dir not supplied, defaulting to working_dir"
            run_log.warning(msg)
            return cls.working_dir
        else:
            return cls._temp_dir

    @temp_dir.setter
    def temp_dir(cls, value: Union[str, Path]):
        """Sets the temporary directory and
        also changes the log handler to write
        in this directory.

        Parameters
        ----------
        value : Union[str, Path]
            Path to new temporary directory.
        """
        cls._temp_dir = value
        change_handler(f"{value}/run.log")

    @property
    def plot_dir(cls) -> Union[str, Path]:
        """The plot directory for outputs.

        Returns
        -------
        str
            Path to the plot directory.
        """
        if cls._plot_dir is None:
            msg = "plot_dir not supplied, defaulting to working_dir"
            run_log.warning(msg)
            return cls.working_dir
        else:
            return cls._plot_dir

    @plot_dir.setter
    def plot_dir(cls, value: Union[str, Path]):
        cls._plot_dir = value

    @property
    def data_dir(cls) -> Union[str, Path]:
        """The data directory for outputs.

        Returns
        -------
        str
            Path to the data directory.
        """
        if cls._data_dir is None:
            msg = "data_dir not supplied, defaulting to working_dir"
            run_log.warning(msg)
            return cls.working_dir
        else:
            return cls._data_dir

    @data_dir.setter
    def data_dir(cls, value : Union[str, Path]):
        cls._data_dir = value


class BaseConfigMethods:
    """Configuring different analyse is critical to a workflow functioning correctly.
    Bill of Materials analysis has a the base Configuration which is inherits a number of
    methods for the Config and a Meta class for properties and setters. An analysis workflow
    can use the BaseConfig directly or inherit the BaseConfigMethods and the MetaConfig to
    customise the configuration parameters.

    The base config includes a number of variables which can be used by BOM Analysis and
    are covered in the other sections such as the MaterialsSelector, the defaults for the
    Material and the Parameters, and a number of different working directories.

    A configuration can also be loaded and dumped to a dictionary using the same method
    names as the Engineering Components.
    """

    _login_details : Dict[str,Optional[str]] = {"username": None, "password": None, "domain": None}
    _materials = MaterialSelector()
    _translations = None
    _default_param_type = "bom_analysis.parameters.PintFrame"
    _default_material = "bom_analysis.materials.MaterialData"
    _parameters = None
    _parts = None
    _working_dir = os.getcwd()
    _temp_dir = None
    _plot_dir = None
    _data_dir = None
    _restrict_param = False

    @classmethod
    def define_config(cls, config_dict: dict = {}, config_path: Optional[Union[str, Path]] = None):
        """defines the config file.

        The config can be loaded from a supplied dictioanry
        or from a path. The intention in using a classmethod
        is that the config can be imported at any stage in
        a process after initialisation without reloading.

        Parameters
        ----------
        config_dict : dict
            A dictionary containing the config file.
        config_path : str
            A string containing the config file location."""
        config = {}
        if config_path is not None:
            with open(Path(config_path), "r") as f:
                config = json.load(f)
        UpdateDict(config, config_dict)
        cls.update_config(**config)

    @classmethod
    def update_config(cls, **kwargs):
        """
        Updates the config from given key word arguments.

        As Config utilises classmethods an classmethod is
        required to update it.

        Parameters
        ----------
        kwargs : dict, optional
            Key is attribute, value will be set.
        """
        for key, val in kwargs.items():
            setattr(cls, key, val)

    @classmethod
    def to_dict(cls) -> dict:
        """Converts the configuration into a dictionary format.

        A check is used so that properties, instances and variables
        within the BaseCLass are not output.

        Returns
        -------
        dict
            A dictionary containing all the variables
            specific to the class.
        """
        variables = dict()
        for key, val in vars(cls).items():
            check = [
                isinstance(val, property),
                isinstance(val, classmethod),
                key in vars(BaseClass).keys(),
            ]
            if not any(check):
                variables[key] = val
        return variables

    @classmethod
    def input_login_details(cls, domain: str = ""):
        """
        Inputs login details.

        This method stores login details if they are required.

        Parameters
        ----------
        domain : str, optional
            The domain for any login details.
        """
        cls._login_details["username"] = str(input("username: "))
        cls._login_details["password"] = str(getpass())
        cls._login_details["domain"] = domain

    @classmethod
    def login_details(cls) -> dict:
        """Runs the login details update if any of the
        values are None.

        Returns
        -------
        dict
            The populated login details."""
        if None in list(cls._login_details.values()):
            cls.input_login_details()
        return cls._login_details


class BaseConfig(BaseConfigMethods, metaclass=MetaConfig):
    """
    Having a configuration that can be shared across all analysis
    ran on the bill of materials is key to running complex workflows.
    The configuration could include features of the Bill of Materials
    such as being able to dynamically add new parameters or information
    for analysis tools such as working directory or login details.

    Bill of Materials Analysis features such a class that can be imported
    without initialisation and with data shared using it.
    """

    pass


class BaseFramework:
    """A base framework class that contains a config attribute
    that can be referenced by BOM analysis or other codes.

    A basic framework was created and is the parent to a number
    of classes within BOM analysis to allow for external configurations
    to be assigned without having to Monkey Patch.

    Attributes
    ----------
    _configuration : BaseConfig
        The configuration that will be used throughout BOM Analysis.
    """

    _configuration = BaseConfig


class BaseClass:
    """
    A key feature of the Bill of Materials analysis is that objects
    can be written and read from a serialisable dictionary. The dictionary
    of the bill of materials is known as the Skeleton and a read and write to
    skeleton feature is included in the parent BaseClass of all bill of
    material objects.

    The skeleton is key for transfering information. It can either be built
    by parsing together a set of dictionaries and then read to create a bill
    of materials or written as an output of a pre-assembled Bill of Materials.

    The skeleton offers a number of benefits, it is generally the primary output
    of analysis ran on the bill of materials, therefore, recording the state of
    the inputs for that analysis (this can be particularly important for transfering
    data in between Model Based System Engieering workflows).
    """

    def to_dict(self, exclusions: list = []) -> dict:
        """
        Exports the data of the base class as a dictionary
        for use in a skeleton of the BOM.

        Parameters
        ----------
        exclusions : list, optional
            A list of attribute strings to be excluded from
            the dump to dictionary.

        Returns
        -------
        dict
            A dictionary containing the base class data.
        """
        dump = {}
        for (name, value) in self.__dict__.items():
            if name not in exclusions:
                dump[name] = encoder(value)
        if "class_str" not in dump or dump["class_str"] is None:
            dump["class_str"] = [f"{self.__module__}.{self.__class__.__name__}"]
        return dump

    def from_dict(self, data: dict):
        """
        Reads and populates from json.

        Parameters
        ----------
        data : dict
            Loaded json.
        """
        for name, sub in data.items():
            if hasattr(getattr(self, name, None), "from_dict"):
                getattr(self, name).from_dict(sub)
            else:
                setattr(self, name, decoder(sub))


class DFClass(BaseClass):
    """The DFClass is included in BOM analysis to allow for
    data to be stored in a dataframe but with some additional
    functionality.

    This functionality includes printing with tabulate, reading and
    writing to a serialisable dictionary, and loading pint quantities."""

    def __init__(self):
        """initialisations of dataframe storage class.

        Attributes
        ----------
        data : pd.DataFrame
            Underlying DataFrame.
        compiled : bool
            Whether the dataframe is compiled from other sources."""
        self.data = None
        self.compiled = None

    @property
    def vars(self) -> np.ndarray:
        """The variables in the data.

        Returns
        -------
        np.ndarray
            An array of the dataframe index, if exist."""
        if isinstance(self.data, pd.DataFrame) is False:
            return np.array([])
        else:
            return np.array(self.data.index)

    @property
    def col_count(self) -> Union[None, Any]:
        """The column count in the wrapped dataframe.

        Returns
        -------
        int
            Interger if a dataframe exists.

        Note
        ----
        As the DataFrame is checked and mypy finds it to return
        Any, the output of the shape is also found to return any.
        """
        if isinstance(self.data, pd.DataFrame) is False:
            return None
        else:
            return self.data.shape[1]

    def create_df(self, number_of_cols: int, *args):
        """Defines the dataframe.

        Parameters
        ----------
        number_of_cols : int
            Number of columns in the DataFrame.
        args : arguments, optional
            The row titles of the DataFrame.

        See Also
        --------
        pandas.DataFrame : Main storage class.
        """
        index = np.append(self.vars, args)
        matrix = (len(index), number_of_cols)
        self.data = pd.DataFrame(np.full(matrix, None), index=index)

    def assign(self, assignee: np.ndarray):
        """
        A method for assigning columns to a dataframe.

        Parameters
        ----------
        assignee : np.ndarray
            The array to be assigned to the dataframe.

        Note
        ----
        See below for additional information.
        https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html
        """
        if isinstance(self.data, pd.DataFrame):
            self.data = pd.concat([self.data, assignee], axis=1, ignore_index=True)
        else:
            self.data = pd.DataFrame(data=assignee)

    def add_to_col(self, col: int, data_dict: dict):
        """Adds data to preexisting rows.

        Parameters
        ----------
        data_dict : dict
            Dictionary with self._variables as keys containing
            data to add.
        col : int
            An integer for the DataFrame column number to be added."""
        for key, val in data_dict.items():
            self.data.at[key, col] = val

    def __repr__(self) -> str:
        """Prints the information.

        To allow for printing i the console, the terminal size
        is checked and the dat wrapped to fit. Additionally,
        pint quantities are formated for readability.

        Returns
        -------
        str
            The string that will be output contianing a
            terminal fitted tabulate based dataframe.

        Note
        ----
        When tabulate is updated we can use
        terminal_size = os.get_terminal_size()
        width = int(terminal_size.columns/(self._col_count+1))
        widths = [width for i in range(0, self._col_count)]
        tabulate(self.data, tablefmt="fancy_grid", maxcolwidths=widths)."""
        terminal_size = os.get_terminal_size()
        width : int = int((terminal_size.columns - 50) / (self.col_count))

        def format(x):
            if hasattr(x, "magnitude"):
                x = Q_(np.format_float_scientific(x.magnitude, precision=4), x.units)

            text_list = textwrap.wrap(str(x), width=width)
            string = "".join([f"{text}\n" for text in text_list])
            return string

        display_data = self.data.copy(deep=True)
        for i_col in range(0, display_data.shape[1]):
            display_data.iloc[:, i_col] = display_data.iloc[:, i_col].apply(format)
        string = ""
        if self.data is not None:
            string += (
                f'\n\n{tabulate(display_data.sort_index(), tablefmt="fancy_grid")}\n\n'
            )
        else:
            string += f"\n\nno data populated\n\n"
        return string

    def to_dict(self, exclusions=[]) -> dict:
        """Exports the data for storage in a json file.

        The encoding to a json serialisable form has to be defined,
        it is not applied as an encoder to the json funciton.

        Returns
        -------
        dump : dict
            A dictionary containing all the class inforamtion
            in a json serialisable format.

        See Also
        --------
        framework.utils.encoder : Converts objects to json serialisable.

        Note
        ----
        The orient=split is to ensure that the correct order
        is maintained - this can be used for visualising
        thermal resistors."""
        dump = {}
        for (name, value) in self.__dict__.items():
            if name == "data" and isinstance(value, pd.DataFrame):
                df_dict = value.to_dict(orient="split")
                dump[encoder(name)] = encoder(df_dict)
            else:
                dump[encoder(name)] = encoder(value)

        if "class_str" not in dump or dump["class_str"] is None:
            dump["class_str"] = [f"{self.__module__}.{self.__class__.__name__}"]
        return dump

    def from_dict(self, data: dict):
        """Reads and populates from json.

        Loads in the parent class and then populates the dataframe if
        required.

        Parameters
        ----------
        data : dict
            loaded json."""
        super().from_dict(data)
        if self.data is not None:
            try:
                self.data["columns"] = np.array(
                    [int(col) for col in self.data["columns"]]
                )
            except:
                pass
            self.data = pd.DataFrame(
                data=self.data["data"],
                columns=self.data["columns"],
                index=self.data["index"],
            )

    def compile_all_df(self, assembly: Any, child_str: str):
        """Compiles all dataframes for a given storage_str
        into a mutable top level dataframe.

        Parameters
        ----------
        child_str : str
            a string attribute name for the information to be extracted from.
        assembly : Any
            the assembly which contains the storage information."""
        self.compiled = child_str
        storages = np.array(
            [
                output[child_str]
                for key, output in assembly.lookup(child_str).items()
                if output[child_str] is not None
                and key != assembly.ref
                and hasattr(output[child_str].data, "empty")
                and not output[child_str].data.empty
            ]
        )
        for stores_in_component in storages:
            self.assign(stores_in_component.data)
