import builtins
from collections import Counter
import importlib
import inspect
import itertools
import logging
from pathlib import Path
import os
from typing import Any, Union

import json
import numpy as np
import pandas as pd

from bom_analysis import ureg, run_log, nice_format, info_handler, Q_


def __init__(self, inherited_classes):
    """Used to add to class factory created classes
    to perform initialisation when there is inhertiance.

    Parameters
    ----------
    inhertied_classes : list
        A list of the classes a component will inherit from."""
    for inherit in inherited_classes:
        inherit.__init__(self)


def encoder(obj):
    """An encoder to ensure all outputs are serialisable.

    Could be turned into a json encoder but
    problems with all the data types with recursion.

    Parameters
    ----------
    obj : type
        An instance of an object which will be
        converted to a serialisable if exist in list.

    Returns
    -------
    type
        The serialisable version of the input instance, if
        the type is specified in the list.

    Note
    ----
    See here for how to turn into a proper encoders
    https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable."""

    if hasattr(obj, "to_dict"):
        obj_dict = obj.to_dict()
        return {encoder(key): encoder(val) for key, val in obj_dict.items()}
    if inspect.ismethod(obj):
        return obj.__name__
    if isinstance(obj, np.float64):
        return obj.item()
    if isinstance(obj, np.int64):
        return obj.item()
    if hasattr(obj, "units") and hasattr(obj, "magnitude"):
        return str(obj.to_base_units().to_root_units())
    if isinstance(obj, str):
        return str(obj)
    if isinstance(obj, list):
        return [encoder(item) for item in obj]
    if isinstance(obj, np.ndarray):
        return np.array([encoder(item) for item in obj]).tolist()
    if isinstance(obj, dict) and not isinstance(obj, Counter):
        return {encoder(key): encoder(val) for key, val in obj.items()}
    if isinstance(obj, dict) and isinstance(obj, Counter):
        output = {encoder(key): encoder(val) for key, val in obj.items()}
        output["_counter"] = "True"
        return output
    return obj


def decoder(obj):
    """Creates a consistance data type for strings, floats, ints and list.

    The aim is to use numpy types throughout the bom_analysis -
    decoder helps ensure this standard format.

    Parameters
    ----------
    obj : type
        An instance to be converted into the standard bom format.

    Returns
    -------
    type
        An object in the standard bom format.

    Note
    ----
    Does not return the string as pint converts to int or float
    The check to see if first value is a float to ensure, particularly
    mass being converted to milliarcsecond, does not convert pure
    strings to units."""
    if hasattr(obj, "from_dict") and isinstance(obj, pd.DataFrame) == False:
        return obj.from_dict()
    if isinstance(obj, str):
        try:
            obj_list = obj.split(" ")
            float(obj_list[0])
            return ureg(obj)
        except:
            return obj
    if isinstance(obj, float):
        return np.float64(obj)
    if isinstance(obj, int):
        return np.int64(obj)
    if isinstance(obj, list):
        result = [decoder(item) for item in obj]
        check = [hasattr(item, "magnitude") for item in result]
        if True in check:
            return np.array(result, dtype=object)
        else:
            return np.array(result)
    if isinstance(obj, dict) and "_counter" not in obj:
        return {decoder(key): decoder(val) for key, val in obj.items()}
    if isinstance(obj, dict) and "_counter" in obj:
        return Counter({decoder(key): decoder(val) for key, val in obj.items()})
    return obj


def change_handler(new_path):
    """Changes the logging handler.

    When running a parameter sweep, it is beneficial to
    have the log for a run in the output files of that
    run. This is done within bom_analysis by changing
    the logging handler path.

    Parameters
    ----------
    new_path : str
        The new path for the run log to be stored."""
    run_log.removeHandler(info_handler)
    info_handler.flush()
    info_handler.close()
    new_info_handler = logging.FileHandler(Path(new_path), "w")
    new_info_handler.setLevel(logging.INFO)
    new_info_handler.setFormatter(nice_format)
    run_log.addHandler(new_info_handler)


def class_factory(name, class_strings, class_data={}):
    """Method for dynamically creating classes.

    The classes are specified as a list of strings
    within the class_strings. The class based on the
    string is created with type and initialised.

    Parameters
    ----------
    class_strings : list
        List of class strings.
    class data : dictionary
        The data to be added as attributes to the created class.

    Returns
    -------
    type
        A new, initialised class created from the input
        class list and data."""
    inherited_classes = tuple(
        class_from_string(class_string) for class_string in class_strings
    )
    new_class = type(name, inherited_classes, {"__init__": __init__})(inherited_classes)
    for name, val in class_data.items():
        setattr(new_class, name, val)

    if hasattr(new_class, "class_str") == False:
        new_class.class_str = class_strings

    return new_class


def class_from_string(string):
    """Creates a class from a string in order to assign custom
    classes to a sub assembly.

    Parameters
    ----------
    string : str
        A string representing a class location.

    Note
    ----
    The importlib must be supplied a package, if the class_str starts with ..
    .. allows for the module to specified and the code could be changed as follows:
    module = importlib.import_module(module_name, package=".materials_model").
    """
    if "." in string:
        module_name, class_name = string.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    else:
        return getattr(builtins, string)


class MaterialSelector:
    """
    The MaterialSelector can select a material database based on a priority order
    and the availability of the material within the database. To perform this function
    the material selector should be supplied with the databases (generally children of the
    MaterialData class).

    To add the databases to the material selector the add_database method can be used with
    the add order assumed to be the priority.

    If the selector was provided a ASME materials database followed by a CoolProp database
    followed by a in-house database during setup, then the material for a component can
    be returned by the select_database method. Say the material is Beryllium, the MaterialSelector
    will check the ASME database, then the CoolProps, then the in-house until it finds (or not)
    Beryllium.

    One of the benefits of using MaterialSelector (and storing it in the Configuration) is that
    when a material is not within one database the next can be checked as discussed in the MaterialData.
    """

    def __init__(self):
        """The material selector is a class that can be provided with
        a list of MaterialData classes in a priotised order from which
        a material can be selected based on a material str.
        """
        self.clear_database()
        
    def clear_database(self):
        """Clears the material databases within the materials 
        selector.
        
        Attributes
        ----------
        priority_order : np.ndarray
            An array contianing information about each of the material
            data class.        
        """
        self.priority_order = np.array([], dtype=object)

    def select_database(self, material_str: str):
        """Selects a material database from a material name.

        Parameters
        ----------
        material_str : str
            A string of the material name which will be checked
            within a database.

        Returns
        -------
        instance
            An initialised database that has been found for a material_str.

        Raises
        ------
        ValueError
            If a database cannot be found.
        """
        for database in self.priority_order:
            if database["material"].check(mat=material_str, **database["data"]):
                return self.intialised_database(material_str, database)
        msg = f"{material_str} doesn't exist in the database {database}"
        run_log.error(msg)
        raise ValueError(msg)

    def intialised_database(self, material_str: str, database: dict):
        """Initialises a datbase class and sets teh attributes from
        the extra data suplied.

        Parameters
        ----------
        material_str : str
            A string of the material name.
        database : dict
            The database contiaing the class and extra data
            {material:class, data:extra data dict}.

        Returns
        -------
        MaterialData
            An initialised class of material data.
        """
        material = database["material"](mat=material_str)
        for key, val in database["data"].items():
            setattr(material, key, val)
        return material

    def add_database(self, database_class, additional_data: dict = {}):
        """Adds a database to the prioritity order
        in the correct fromat.

        Parameters
        ----------
        database_class : MaterialData
            Class of material data.
        additional_data : dict, optional
            Any additional data within will be added to the
            database_class.__dict__, by default {}.
        """
        database = dict(material=database_class, data=additional_data)
        self.priority_order = np.append(self.priority_order, database)

    def to_dict(self):
        """Converts the MaterialSelector to a dictionary.

        Adds a set of class_str so the the priority order can be
        created from a string.

        Returns
        -------
        dict
            A dictionary of the material selector.
        """
        dump = []
        for database in self.priority_order:
            if hasattr(database["material"], "class_str"):
                class_strings = database["material"]["class_str"]
            else:
                class_strings = [
                    f"{database['material'].__module__}.{database['material'].__name__}"
                ]
            dump.append({"class_str": class_strings, "data": database["data"]})
        return dump

    def old_style_from_dict(self, data: dict):
        """Older versions of settings files contain
        a non-object orientated materl priority order which
        can be imported by this method.

        Parameters
        ----------
        data : dict
            An old style dictionary containin an 'order' key.

        Raises
        ------
        ValueError
            If a class str has more that on class_str as it cannot
            inherit a single name.
        """

        order = data["order"]
        for i_order in range(0, len(order.keys())):
            material_database = order[str(i_order)]
            material_class_data = data[material_database]
            if len(material_class_data["class_str"]) > 1:
                msg = "material class string has more than one component"
                run_log.error(msg)
                raise ValueError(msg)
            # material_class_data["class_str"] = material_class_data["class_str"][0]
            material_class = class_from_string(material_class_data["class_str"][0])
            self.add_database(
                database_class=material_class, additional_data=material_class_data
            )

    def from_dict(self, data: dict):
        """Reads a dictionary and populates the MaterialSelector.

        Resets the priority order so that the same MaterialData classes
        are not added numerous times.

        Parameters
        ----------
        data : dict
            A database with the information to form the MaterialSelector.
        """
        self.priority_order = np.array([], dtype=object)
        if "order" in data:
            self.old_style_from_dict(data)
        else:
            for database in data:
                material_class = class_from_string(database["class_str"])
                database["data"]["class_str"] = database["class_str"]
                self.add_database(
                    database_class=material_class, additional_data=database["data"]
                )


class Translator:
    """Translating strings can be very important to a bill of materials
    and a workflow due to mismatches in the naming is common across
    material libraries (both the name and the parameters).

    The translator can be defined from a dictionary and utilises classmethods
    so can be used without initialisation. After the underlying data has been
    populated, the input for translation can be supplied alongside the output format."""

    _data = {}

    def __new__(cls, name, output_format):
        """Translates a name into a chosen output.

        Parameters
        ----------
        name : str
            Name to be translated.
        output : str
            Output format for name to be translated to.

        Returns
        -------
        output_name : str
            The translated name of the input name if it
            exists within the translation data/output format."""
        if name not in cls._data:
            output_name = name
        else:

            if output_format in cls._data[name]:
                output_name = cls._data[name][output_format]["name"]
                if "msg" in cls._data[name][output_format].keys():
                    logging.info(cls._data[name][output_format]["msg"])
            else:
                output_name = name
        return output_name

    @classmethod
    def define_translations(cls, locations):
        """Defines the translations for the class.

        Parameters
        ----------
        locations : list
            List of translation file locations."""
        cls._data = load_and_merge(locations)

    @classmethod
    def available_inputs(cls):
        """Produces a list of all the input translations
        for the loaded translator.

        Returns
        -------
        list
            The input translations."""
        return list(cls._data.keys())


class PrintParamsTable:
    def format_params(self, list_of_params: list) -> list:
        """Formats the dictionary representation of the parameters to allow
        for nice string represntation.

        If being used in a terminal, the size will be checked to split
        the strings of the information in the parameter so that the
        output does not extend over multiple lines (and can be read).
        The in-built pint formater is used to convert the strings representing
        a unit (if supplied) to symbolic i.e. meter to m.

        Parameters
        ----------
        list_of_params : list
            A list of dictionaries with the _data parameters.

        Returns
        -------
        list
            A formated list of dictionaries with the _data parameters.
        """
        formated_list_of_params = []
        max_character = self.get_max_column_width(list_of_params)
        for param in list_of_params:
            new_param = {}
            if "unit" in param and param["unit"] is not None:
                param["unit"] = format(Q_(param["unit"]).units, "~")
            elif "unit" in param:
                param["unit"] = "dimensionless"
            for key in self.header:
                shortened_pint = self.shorten_unit(param[key])
                split_string = self.new_line_in_string(shortened_pint, max_character)
                new_param[key] = split_string
            formated_list_of_params.append(new_param)
        return formated_list_of_params

    def get_max_column_width(self, list_of_params: list) -> Union[int, None]:
        """Gets the maximum column size for printing of
        a tabular dataframe.

        The maximum column size is important as it allows
        a string to be split over multiple lines and, therefore,
        displayed nicely.

        Parameters
        ----------
        list_of_params : list
            List of parameters that will be used to determine
            the maximum size of the columns in the print.

        Returns
        -------
        int
            The maximum column size for a given terminal width.
        None
            If an OSError is raised (due to no terminal) or
            an index error is raised (due to an empty input list).
        """
        try:
            terminal_size = os.get_terminal_size().columns
            return int(terminal_size / len(list_of_params[0]))
        except (
            OSError,
            IndexError,
        ):
            return None

    def shorten_unit(self, quantity: Any) -> Any:
        """Shortens the format of the units in a pint unit
        and returns as string.

        Parameters
        ----------
        quantity : Any
            Any input to be tried to have the units
            converted to symbolic via the format.

        Returns
        -------
        str
            String for quantity with shortened units.
        """
        try:
            return format(quantity, "~")
        except (
            ValueError,
            TypeError,
        ):
            return quantity

    def new_line_in_string(self, input: Any, max_character: int = None) -> Any:
        """Splits the input into multiple lines based on a supplied
        max character interger.

        Parameters
        ----------
        input : Any
            The parameter item to be split.
        max_character : int, optional
            The maximum number of characters before adding the new
            line, by default None.

        Returns
        -------
        Any
            The parameter item with the split accross new lines added.
        """
        if max_character is not None:
            try:
                lines = []
                for i in range(0, len(input), max_character):
                    lines.append(input[i : i + max_character])
                return "\n".join(lines)
            except TypeError:
                return input
        else:
            return input


class UpdateDict:
    """Updating a dictionary with more control
    over than the inbuilt is important when
    parsing jsons to build the skeleton.

    This function allows for that control."""

    def __init__(self, main, *args, **kwargs):
        """Initialises the update dictionary.

        Mutability is used to get this class to
        work, thefore, losing that mutability stops it.
        Particular data types can be locked by supplying them
        in the kwargs, this means that some values cannot
        be overwritten without an error, defaults are
        int and float.

        Parameters
        ----------
        main : dictionary
            The main dictionary which will be updated.
        args : tuple
            The input dictionaries which main will be
            updated with.
        kwargs : dict
            The keyword argments that can be supplied,
            locked is the only one used.

        Note
        ----
        Kwargs could be replaced with a default parameter
        for locked.
        """
        self.main = main
        self.input = args
        self.build()

    def build(self):
        """Updates the main dictionary with the input
        attribute."""
        self.update_main(self.main, self.input)

    def unique_keys(self, input_dict):
        """Defines the unique keys in all the input dict.

        Parameters
        ----------
        input_dict : dict
            The input dictionary.

        Returns
        -------
        dict
            A dictionary of the input keys, a dictionary
            for legacy reasons."""
        temp = {}
        for val in input_dict:
            temp.update(val)
        return temp.keys()

    def update_main(self, main, input_dict):
        """Updates the main dictionary with the input
        dictionary.

        Parameters
        ----------
        input_dict : dict
            The input dictionary.
        main : dictionary
            The main dictionary which will be updated.
        """
        unique = self.unique_keys(input_dict)
        for key, data in itertools.product(unique, input_dict):
            if key in main and key in data:
                self.update_key(main, key, data)
            elif key in data:
                main[key] = data[key]

    def update_key(self, main, key, data):
        """Updates the data in the main dictionary
        with a key.

        Parameters
        ----------
        main : dictionary
            The main dictionary which will be updated.
        key : str or int
            The key in the main dictioanry which will
            have the value updated with data.
        data : type
            The data which will be added to the main
            dict with key.

        Raises
        ------
        ValueError
            If data type in .locked is trying to be overwritten."""
        main_type = type(main[key])
        if main_type == type(data[key]):

            if main_type == str:
                logging.info(f"overwriting {key}={main[key]} with {data[key]}")
                main[key] = data[key]
            elif main_type == int or main_type == float:
                main[key] = data[key]
            elif main_type == dict:
                self.update_main(main[key], (data[key],))
            elif main_type == list:
                main[key] += data[key]
        else:
            if main[key] is not None and data[key] is not None:
                run_log.warning(
                    (
                        f"Data type changed in dictionary update.\n"
                        f"{main} {key} data types\nmain={type(main[key])}"
                        f"\ndata={type(data[key])}"
                    )
                )
            main[key] = data[key]


def load_and_merge(location_list):
    """Merges multiple json dicts into a single dictionary.

    This is used for when parsing jsons to build the
    skeleton. It allows a list of locations to
    be supplied within the settings or config.

    Parameters
    ----------
    location_list : list
        List of the locations of json which will
        be loaded and merged.

    Returns
    -------
    merged : dict
        A merged dictionary of all the json
        in the location list.
    """
    merged = {}
    for path in location_list:
        with open(Path(path), "r") as f:
            dictionary = json.load(f)
        UpdateDict(merged, dictionary)
    return merged


def access_nested(obj, location, pos=0):
    """Accesses data within a nested object
    by searching for attribute or item down
    a list/tuple/array.

    Parameters
    ----------
    obj : instance
        The object to be accessed.
    location : iterable
        The iterable location of the data.
    pos : int, optional
        The position of the nested dictionary to be
        accessed, defaults to 0.

    Returns
    -------
    data : instance
        The data which is returned."""
    loc = location[pos]

    pos += 1

    if hasattr(obj, loc):
        if pos == len(location):
            data = getattr(obj, loc)
        else:
            data = access_nested(getattr(obj, loc), location, pos=pos)
    elif isinstance(obj, dict) and loc in obj:
        if pos == len(location):
            data = obj[loc]
        else:
            data = access_nested(obj[loc], location, pos=pos)
    else:
        data = None

    return data
