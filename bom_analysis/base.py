from builtins import getattr, hasattr
import types
from pathlib import Path
import os
import textwrap
from getpass import getpass

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
)


class ConfigurationNotFullyPopulated(Exception):
    """An exception for when the configuration is not
    populated correctly with all the information required
    for a method to function correctly.
    """

    pass


def add_base_class(existing_object, import_method, export_method):
    """Adds an import and export function to a class under the
    name export_data and import_data.

    This is currently unused and maybe should be removed.
    The original intention was to be able to add methods
    to allow json compatible output dictionaries to
    external functions.

    Parameters
    ----------
    existing_object : instance
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
    Information about how the configuration works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Analysis.html#configuring-analysis>`_.
    """

    @property
    def materials(cls):
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
        return cls._materials

    @materials.setter
    def materials(cls, value):
        """Setter for the materials.

        Parameters
        ----------
        value : dict
            Material data to be assigned.
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
    def parameters(cls):
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
    def translations(cls):
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
    def parts(cls):
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
    def working_dir(cls):
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
    def default_param_type(cls):
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
    def temp_dir(cls):
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
    def temp_dir(cls, value):
        cls._temp_dir = value

    @property
    def plot_dir(cls):
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
    def plot_dir(cls, value):
        cls._plot_dir = value

    @property
    def data_dir(cls):
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
    def data_dir(cls, value):
        cls._data_dir = value


class BaseConfigMethods:
    """Information about how the configuration works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Analysis.html#configuring-analysis>`_.

    Attributes
    ----------
    _login_details : dict
        Login details that could be supplied by the config.
    _materials : MaterialSelector
        The class for selecting a material library from a string.
    _translations : list
        The list of translation file locations.
    _default_param_type : str
        The class string for the default parameterframe type
        that will be used by the bill of materials.
    _default_material : str
        The class string for the default material class that
        will be used by the bill of materials.
    _parameters : list
        List of file locations that contain the parameters
        that can be used to build a skeleton.
    _parts : list
        List of file locations that contain the parts that
        can be used to build as skeleton.
    _temp_dir : str
        Location of the temporary directory.
    _plot_dir : str
        Location of the directory which plots will be output to.
    _data_dir : str
        Location of the directory which contains data used by the
        analysis.
    _restrict_param : boolean
        True/False on whether parameters can be added to the parameter 
        frame on the fly.
    """

    _login_details = {"username": None, "password": None, "domain": None}
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
    def define_config(cls, config_dict={}, config_path=None):
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
    def to_dict(cls):
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
    def input_login_details(cls, domain=""):
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
    def login_details(cls):
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
    Information about how the configuration works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Defining_a_Bill_of_Materials.html#a-global-configuration>`_.
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
    Information about how the BaseClass and Skeletons work can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Defining_a_Bill_of_Materials.html#the-skeleton>`_.
    """

    def to_dict(self, exclusions=[]):
        """
        Exports the data for storage in a json file.

        Parameters
        ----------
        exclusions : list, optional
            A list of attribute strings to be excluded from
            the dump to dictionary.
        """
        dump = {}
        for (name, value) in self.__dict__.items():
            if name not in exclusions:
                dump[name] = encoder(value)
        if "class_str" not in dump or dump["class_str"] is None:
            dump["class_str"] = [f"{self.__module__}.{self.__class__.__name__}"]
        return dump

    def from_dict(self, data):
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
    """
    Information about how the DataFrame Class works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Variables.html#wrapped-dataframe>`_.
    """

    def __init__(self):
        """initialisations of dataframe storage class."""
        self.data = None
        self.compiled = None

    @property
    def vars(self):
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
    def col_count(self):
        """The column count in the wrapped dataframe.

        Returns
        -------
        int
            Interger if a dataframe exists.
        """
        if isinstance(self.data, pd.DataFrame) is False:
            return None
        else:
            return self.data.shape[1]

    def create_df(self, number_of_cols, *args):
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

    def assign(self, assignee):
        """
        A method for assigning columns to a dataframe.

        Parameters
        ----------
        assignee : np.ndarray
            The array to be assigned to the dataframe.

        Note
        ----
        `See <https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html>`_ 
        for additional information.
        
        """
        if isinstance(self.data, pd.DataFrame):
            self.data = pd.concat([self.data, assignee], axis=1, ignore_index=True)
        else:
            self.data = pd.DataFrame(data=assignee)

    def add_to_col(self, col, data_dict):
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

    def __repr__(self):
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
        width = int((terminal_size.columns - 50) / (self.col_count))

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

    def to_dict(self):
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

    def from_dict(self, data):
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

    def compile_all_df(self, assembly, child_str):
        """Compiles all dataframes for a given storage_str
        into a mutable top level dataframe.

        Parameters
        ----------
        child_str : str
            a string attribute name for the information to be extracted from.
        assembly : BoM instance
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
