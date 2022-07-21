from collections.abc import Iterable
import pprint
from typing import Any, Dict, Optional, Union

from box import Box
import numpy as np
from pint.errors import UndefinedUnitError
from tabulate import tabulate

from bom_analysis import Q_, run_log
from bom_analysis.base import BaseFramework
from bom_analysis.utils import access_nested, encoder, decoder, PrintParamsTable


class MissingParamError(AttributeError):
    """Error when a parameter is not in
    the data.
    """

    pass


class FlexParam:
    """
    Flexible parmeter is a wrapper for a non-mutable box.

    The keys of the box are flexible and utilise class attributes
    so that the keys are shared across all instances.

    Attributes
    ----------
    _required_keys : np.array
        The keys required by the parameter, will raise a key
        error if not supplied.
    _additional_keys : np.array
        The additional keys that are shared across all instances of
        the flexible parameter.

    Note
    ----
    The recommended keys are below.

    var: str
        The short parameter name.
    name: str
        The long parameter name.
    value: float
        The value of the parameter.
    unit: str
        The unit of the parameter.
    source: str
        The source (reference and/or code) of the parameter.
    """

    _required_keys: np.ndarray = np.array(["var", "value"])
    _additional_keys: np.ndarray = np.array([])

    def __init__(self, val: Box):
        """Initialisation of the flexible parameter.

        Parameters
        ----------
        val : dict
            A dictionary containing the parameter data.

        Note
        ----
        The typing return should be Union[dict, Box] and not Box
        but assymetric setters are not yet working. See mypy
        issue 3004.
        """
        self._data: Box = Box({}, frozen_box=True)
        self.data = val

    @property
    def data(self) -> Box:
        """Property for the primary data store that
        contains the frozen box under the private
        _data variable.

        The property runs and update before returning
        the private _data to add any additional keys
        to the returned box.

        Returns
        -------
        Box
            The parameter data store.
        """
        self.update()
        return self._data

    @data.setter
    def data(self, data: Union[dict, Box]):
        """The setter for the data property.

        Performs a set of checks on the inputs such as checking that
        the correct keys are supplied, processes the inputs
        so that any additional keys are added, and then creates
        a new frozen box for the parameter.

        Parameters
        ----------
        data : Union[dict, Box]
            The data to be input to the box storage, must
            contain the _required_keys as keys.
        """
        self.check_inputs(data)
        processed: dict = self.process_inputs(data)
        self._data = Box(processed, frozen_box=True)

    def check_inputs(self, data: Union[dict, Box]):
        """Checks that the input is correct by comparing
        the ._required_keys attribute to the data.

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.

        Raises
        ------
        KeyError
            If the keys do not match.
        """
        for key in data.keys():
            if data[key] == "None":
                data[key] = None
        if not np.all(np.isin(self._required_keys, np.array(list(data.keys())))):
            raise KeyError(
                f"{data} does not have all the required keys ({self._required_keys})"
            )

    @classmethod
    def process_inputs(cls, value: Union[dict, Box]) -> dict:
        """Processes the inputs to the data to
        extract any new keys and write them to the
        _additional keys class attribute.

        Also assigns None if any of the additional
        keys are not supplied.

        Parameters
        ----------
        value : Union[dict, Box]
            Input variable to the box data store.

        Returns
        -------
        dict
            The processed input with full _required_keys and
            _additional_keys.
        """
        processed: dict = {}
        unique_keys = np.unique(
            np.append(cls._additional_keys, np.array(list(value.keys())))
        )
        for key in unique_keys:
            if not np.isin(key, cls._additional_keys) and not np.isin(
                key, cls._required_keys
            ):
                cls._additional_keys = np.append(cls._additional_keys, key)
            if key not in value:
                processed[key] = None
            else:
                processed[key] = value[key]

        return processed

    def update(self):
        """Updates the private _data with a frozon box for
        a new data set and adds any additional keys
        that were input but not captured in _additional_keys
        attribute.

        Checks fields and updates if they do not match."""
        new_data_dict: dict = {}
        if not np.all(
            np.isin(self._additional_keys, np.array(list(self._data.keys())))
        ):
            new_data_dict = self._data.to_dict()
            for key in self._additional_keys:
                if key not in new_data_dict:
                    new_data_dict[key] = None
            self._data = Box(new_data_dict, frozen_box=True)

    def __getattr__(self, attr_name: str) -> Any:
        """Gets parameter from frozen box if it exists.

        Parameters
        ----------
        attr_name : str
            The name of the attribute which will be returned.

        Returns
        -------
        Any
            The attribute with the attr_name within the frozen box.
        """
        return self.data[attr_name]

    def __getitem__(self, attr_name: str) -> Any:
        """Gets parameter from frozen box if it exists.

        Parameters
        ----------
        attr_name : str
            The name of the attribute which will be returned.

        Returns
        -------
        type
            The attribute with the attr_name within the frozen box.
        """
        return self.data[attr_name]

    def parameter(self) -> Box:
        """returns the frozon box.

        This function is included for backwards compatibility.

        Returns
        -------
        Box
            A frozen box containing the parameter information."""
        return self.data

    def replace(self, **kwargs):
        """Replaces any of the variables in
        the data store with a new value.

        As the data store is designed to be non-mutable
        a new box is created based on the old boxes dictionary
        and the kwargs supplied.
        """
        data_dict = self.asdict()
        for key, value in kwargs.items():
            data_dict[key] = value
        self.data = data_dict

    @property
    def fields(self) -> np.ndarray:
        """Property that returns all the keys in the data store
        by appending the _required_keys and _additional_keys.

        Returns
        -------
        np.ndarray
            The appended _required_keys and _additional_keys.
        """
        return np.append(self._required_keys, self._additional_keys)

    def asdict(self) -> dict:
        """
        Converts the frozen box to a dictionary by using the
        boxes in-built method.

        Returns
        -------
        dict
            The dictionary of the ParameterFrame _data attibute.
        """
        return self.data.to_dict()

    def __str__(self) -> str:
        """
        Return a string representation of the Parameter.

        Returns
        -------
        str
            String representation of the parameter.
        """
        return str(self.data.to_dict())


class PintParam(FlexParam):
    """Parameter with pint integration.

    A child of FlexParam with pint type enforcement for the value."""

    _additional_keys = np.array(["unit"])

    def check_inputs(self, data: Union[dict, Box]):
        """Checks that the input is correct by comparing
        the ._required_keys attribute to the data as per the
        parent class but also checks whether the input has
        a pint quantity, if the input should, and whether it
        is appropriate (consistant dimensionality).

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.

        Raises
        ------
        KeyError
            If the keys do not match.
        """
        super().check_inputs(data=data)
        self.check_for_pint(data)

    def check_for_pint(self, data: Union[dict, Box]):
        """Checks that the correct unit is being supplied.

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.

        Raises
        ------
        ValueError
            If a pint unit is not supplied.
        pint.DimensionalityError
            If the wrong type is supplied."""
        if isinstance(data["value"], str):
            self.check_string(data)
        elif data["value"] is not None:
            self.check_non_string(data)
        self.check_dimensionality(data)

    def check_non_string(self, data: Union[dict, Box]):
        """Checks that a non-strings is supplied with the
        information to create a pint quanitity within
        the input data under the "value" key.

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.

        Raises
        ------
        ValueError
            If not a quantity or a unit is not supplied in data."""
        try:
            data["value"] = data["value"].to_reduced_units()
            unit = data["value"].units
            value = data["value"].magnitude
            dimensionality = data["value"].dimensionality
            data["unit"] = str(unit)
        except AttributeError:
            if "unit" in data:
                data["value"] = Q_(data["value"], data["unit"])
            else:
                raise ValueError(
                    (
                        f"The {data['var']} must be str, have a unit "
                        f"and value, or have a value with unit (such as pint quantity)"
                        f"data=\n{pprint.pformat(data['value'])}"
                    )
                )

    def check_string(self, data: Union[dict, Box]):
        """Checks whether a supplied string in the "value" key
        of the data can form a pint quantity.

        Pint can form a quantity from an input string such as
        '1 meter' which will be interpreted by this parameter.

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.
        """
        try:
            data["value"] = Q_(data["value"])
        except UndefinedUnitError:
            if "unit" in data:
                data["value"] = Q_(data["value"], data["unit"])
            else:
                data["unit"] = "dimensionless"

    def check_dimensionality(self, data: Union[dict, Box]):
        """A parameter cannot change dimensionality, i.e.
        cannot go from being 1m (with the dimensionality [length])
        to 1s (with the dimensionality [time]). This function checks
        that changes to the _data to not violate this.

        Parameters
        ----------
        data : Union[dict, Box]
            The data dictionary to be checked.

        Raises
        ------
        AssertionError
            If the dimensionality is not the same.
        """
        if self.data.unit is not None and not isinstance(data["value"], str):
            assert (
                Q_(data["unit"]).dimensionality == Q_(self.data.unit).dimensionality
            ), (
                "A parameter cannot change"
                f"the unit dimensionality original={data['value'].dimensionality}, new={self.data.value.dimensionality}"
            )

    def asdict(self) -> dict:
        """
        As the parent class, uses the in-built
        to_dict method of the box to return
        the parameter as a dictionary. Additionally
        the method tries to extract the unit from the
        quantity in the 'value' key and return it under
        the 'unit' key as a string.

        Returns
        -------
        dict
            The dictionary of the ParameterFrame.
        """
        dump = super().asdict()
        try:
            value = dump["value"]
            dump["value"] = value.magnitude
            dump["unit"] = str(value.units)
        except AttributeError:
            pass

        return dump


class ParameterFrame(PrintParamsTable):
    """The Parameter class aims to be the primary method for storing parameters within the
    Engineering Objects. A version (either Pint integrated or not) is included with every
    Engineering Object using the attribute params. The default is with Pint integration
    is set within the Config.

    Having a structured method for storing parameters is key to sharing data - it allows
    additional information to be supplied such as the source or an improved description.

    Individual parameters use namedtuple and the parameter database use DataFrames. In addition
    to the name and value that needs to be supplied to the individual parameter any futher information
    can be added as mentioned. If an additional bit of information is included (such as devaiation)
    all parameters will be updated with a empty placeholder for that information.

    The design for parameter handling was inspired by BLUEPRINT (`publication <10.1016/j.fusengdes.2018.12.036>`__)
    """

    class_str = ["bom_analysis.parameters.ParameterFrame"]

    def __init__(self, **kwargs):
        """Initialises the class and populates the
        _data attibute with a Box.

        Attributes
        ----------
        class_str : list
            The class string path to the parameter frame.

        Note
        ----
        The kwargs are left as an input for legacy use.

        """
        self._data: Box = Box()

    def __setattr__(self, attr: str, value: Any):
        """Sets a value in the underlying _data.

        The aim of the ParameterFrame is to allow easy
        access to the Parameters which make up the
        _data. To aid with this, it is possible to
        add new Parameters to the underlying _data of
        the ParameterFrame dynamically if this is allowed
        by the configuration or update the parameter value
        if checks pass. Additionally the class_str and _data can be
        set using the standard magic method and a 'data' attr
        can be given to update the _data.

        Parameters
        ----------
        attr : str
            The name of the parameter to be set.
        value : type
            The value which the parameter will be set to. This
            is the name 'value' in the namedtuple.

        Raises
        ------
        MissingParamError
            If parameter does not exist in the _data."""
        if attr not in ["_data", "data", "class_str"]:
            if attr in self._data:
                self._data[attr].check_inputs(dict(var=attr, value=value))
                self._data[attr].replace(value=value)
            elif (
                attr not in self._data
                and not BaseFramework._configuration.restrict_param
            ):
                self.add_parameter(var=attr, value=value)
            else:
                raise MissingParamError(
                    (
                        f"{attr} not defined in params and cannot be added "
                        "on the fly as restrict_param = True n configuration. To add properly"
                        "use the add_param method"
                    )
                )
        elif attr == "data":
            self.from_dict(value)
        else:
            super().__setattr__(attr, value)

    def __getattr__(self, attr: str) -> Any:
        """
        Returns the value for a parameter name.

        Tries to get the 'value' key from the parameter and raises
        an Error if that key does not exist.

        Parameters
        ----------
        attr : str
            the attibute name to be checked to see if a wrapped named
            tuple exists in _data or as attribute.

        Returns
        -------
        Any
            The value of the specified attribute.

        Raises
        ------
        MissingParamError
            If attr does not exist as a key in _data.
        """
        try:
            return self._data[attr].value
        except KeyError:
            raise MissingParamError(
                f"{attr} does not exist in parameters {list(self._data.keys())}"
            )

    def __iter__(self) -> Iterable:
        """Allows the assembly object to be iterated on to return the
        sub_assembly items.

        Returns
        -------
        iterable
            An iterable of all the Parameters in the data frame.
        """
        return iter(self._data.values())

    def __str__(self) -> str:
        """
        Returns user representation of the ParameterFrame for humans
        to read using tabulate.

        Formats the data to change the column width based on the terminal
        and the unit type to symbols.

        Returns
        -------
        str
            A string format of a tabulate output.

        See Also
        --------
        tabulate.tabulate : nice table formater.
        """
        list_of_params = self.convert_parameter_dictionary_to_list(
            self.to_dict()["data"]
        )
        formated_list_of_params = self.format_params(list_of_params)
        return f"\n{tabulate(formated_list_of_params, headers='keys', tablefmt='fancy_grid')}"

    @property
    def order(self) -> np.ndarray:
        """The order which the params have been
        added to the parameterframe.

        Returns
        -------
        array
            the order the params have been added.
        """
        return np.array(list(self._data.keys()))

    @property
    def header(self) -> np.ndarray:
        """The order which the table output will be given
        based on the order in the _required_keys followed
        by the order in the _additional_keys.

        Returns
        -------
        np.array
            a list in order of the headers for
            printing the parameter frame."""
        header : np.ndarray = self._data[self.order[-1]].fields
        return header

    def add_parameter(self, **kwargs):
        """Adds a parameter to the underlying _data, must be
        supplied with a var key. If not supplied with a value
        a value of None will be added.

        The kwargs are used to be flexible in the addition of
        variables with the checks that the correct keys are
        supplied beiing conducted in the Parameter.
        """
        var = kwargs["var"]
        if "value" not in kwargs:
            kwargs["value"] = None
        self._data[var] = FlexParam(dict(**kwargs))

    def update_parameter(self, var: Optional[str] = None, **kwargs):
        """
        Update full Parameter information (except for var).

        Parameters
        ----------
        kwargs : key word arguments, optional
            The data which makes up a new parameter."""
        param: Union[PintParam, FlexParam] = self.get_param(var)
        param.replace(**kwargs)

    def get_param(self, attr: Optional[str], key: Optional[str] = None) -> Any:
        """Gets a chosen parameter from the parameterframe instead
        of the value.

        This allows return of other parts of the parameter
        so that things like the unit can be accesseed.

        Parameters
        ----------
        attr : Optional[str]
            The attibute name to be checked to see if a wrapped named
            tuple exists in _data or as attribute.
        key : Optional[str]
            The field in the parameter which will be
            returned.

        Returns
        -------
        Any
            The parameter for the given attibute name, can be the Box
            if no key is supplied or the item in the box for the given key.

        Raises
        ------
        MissingParamError
            If the parameter does not exist in the _data or the key does
            not exist in the parameter."""
        try:
            if key is None:
                return self._data[attr]
            else:
                return self._data[attr][key]
        except KeyError:
            raise MissingParamError(
                f"{attr} does not exist in parameters {list(self._data.keys())}"
            )

    def check_param(self, attr: str) -> bool:
        """Checks a parameter exists within the database.

        Parameters
        ----------
        attr : str
            the attibute name to be checked to see if a wrapped named
            tuple exists in _data or as attribute.

        Returns
        -------
        bool
            True/False on whether the parameter exists in _data."""
        if attr in self._data:
            return True
        else:
            return False

    def to_dict(self) -> dict:
        """Dumps the parameter frame to a json serilisable dictionary.

        The class string is included to allow for the BOM analysis to
        recreate the ParameterFrame from a skeleton.

        Returns
        -------
        dict
            A json serialisable dict containing all the data from the
            parameter frame.

        See Also
        --------
        utils.encoder : Encodes to json serialisable dict from the numpy format.
        """
        dump: Dict[str, Union[dict, list]] = {"data": {}}
        if "class_str" not in dump or dump["class_str"] is None:
            dump["class_str"] = self.class_str

        for key, val in self._data.items():
            dump["data"][key] = val.asdict()
            try:
                dump["data"][key]["value"] = dump["data"][key]["value"].magnitude
            except AttributeError:
                pass
        dump = encoder(dump)

        return dump

    def from_dict(self, class_data: dict):
        """Builds the fuction from the stored information.

        Parameters
        ----------
        class_data : dict
            The dictionary which is input to populate the parameter frame.

        See Also
        --------
        utils.decoder : Decodes a json serialisable dict into numpy format."""
        data = decoder(class_data)
        list_of_param_dicts = self.default_from_dict(data)
        for param_dict in list_of_param_dicts:
            self.add_parameter(**param_dict)

    def add_defaults(self, data: dict):
        """Adds default parameters to the parameterframe.

        If the parameter is not in the data and the config
        allows data to be added then the parameters will
        be created from the input dictionary. If the data is
        already in the _data then the parameters will be
        updated.

        Parameters
        ----------
        data : dict
            The data which will be added to the parameterframe.
        """
        list_of_param_dicts = self.default_from_dict(data)
        for param_dict in list_of_param_dicts:
            if (
                param_dict["var"] not in self._data
                and not BaseFramework._configuration.restrict_param
            ):
                self.add_parameter(**param_dict)
            else:
                self.update_parameter(**param_dict)

    def default_from_dict(self, data: dict) -> list:
        """Extracts the information from the data.

        This class allows differnet formats of dictionaries
        to be extracted. This is so that the method can
        accept a skeleton format or a format which is simpler
        for a used.

        Parameters
        ----------
        data : dict
            The dictionary containing the parameter data.

        Returns
        -------
        list
            A list of dictionaries in the format from which a
            Parameter can be created ({var:mass, value:10, unit:10}).
        """
        data = encoder(data)
        parameter_dicts: dict = self.extract_dictionary_of_parameters(data)
        return self.convert_parameter_dictionary_to_list(parameter_dicts)

    def extract_dictionary_of_parameters(self, data: dict) -> dict:
        """Extracts a dictionary of the different parameters supplied
        in the data dictionary.

        Different (and legacy) skeletons can have the parameters in
        different stages of a nested dictionary with different
        keys. This function returns the parameter dictionary
        for each of the various locations.

        Parameters
        ----------
        data : dict
            Nested dictionary containing the parameters.

        Returns
        -------
        dict
            Dictionary of the parameters only.
        """
        if access_nested(data, ["_params", "data"]) is not None:
            parameter_dicts: dict = data["_params"]["data"]
        elif access_nested(data, ["params", "data"]) is not None:
            parameter_dicts = data["params"]["data"]
        elif access_nested(data, ["data"]) is not None:
            parameter_dicts = data["data"]
        else:
            parameter_dicts = data
        return parameter_dicts

    def convert_parameter_dictionary_to_list(self, parameter_dicts: dict) -> list:
        """Converts the paramters contained within _data to
        a list of parameters.

        Includes a try except to caputure any supplied dictionaries
        that contain the var as the key and the value as the value
        of that key e.g. {mass:Q_(1, 'kg')}.

        Parameters
        ----------
        parameter_dicts : dict
            The dictionary of paramters to be converted to a list.

        Returns
        -------
        List
            List of the paramter dictionaries.
        """
        list_of_param_dicts = []
        for key, param_dict in parameter_dicts.items():
            try:
                if "var" not in param_dict:
                    param_dict["var"] = key
                elif param_dict["var"] != key:
                    run_log.warning(
                        (
                            f"supplied key in dictionary ({key}) not equal "
                            f"to supplied by value['var'] ({param_dict['var']})"
                        )
                    )
            except TypeError:
                param_dict = {"var": key, "value": param_dict}
            list_of_param_dicts.append(param_dict)
        return list_of_param_dicts

    def add_basic_parameters(self, parameter_dict: dict):
        """To simplify adding multiple parameters quickly
        this method can be use but does not allow the
        assignment of anything other than the value and var.

        Legacy method that uses the .add_defaults method.

        Parameters
        ----------
        parameter_dict : dict
            dictionary of values to be added to the
            frame where the key is the var.
        """
        self.add_defaults(parameter_dict)


class PintFrame(ParameterFrame):
    """Pint integrated version of the parameter frame."""

    class_str = ["bom_analysis.parameters.PintFrame"]

    def add_parameter(self, **kwargs):
        """Adds a parameter to the underlying _data, must be
        supplied with a var key. If not supplied with a value
        a value of None will be added.

        The kwargs are used to be flexible in the addition of
        variables with the checks that the correct keys are
        supplied beiing conducted in the Parameter.
        """
        var = kwargs["var"]
        if "value" not in kwargs:
            kwargs["value"] = None
        self._data[var] = PintParam(dict(**kwargs))
