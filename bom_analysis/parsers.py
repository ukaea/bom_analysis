from collections.abc import Iterable
import copy
import pprint
from typing import Dict, Tuple, Union

from bom_analysis import run_log, BaseFramework
from bom_analysis.utils import UpdateDict, load_and_merge


class SkeletonParser(BaseFramework):
    """
    Parsing a skeleton is a way of building a skeleton without
    building the bill of materials. It can help speed up the
    creation of new BOM but, as it parsers a number of files,
    operates mostly with .json and is therefore not object orientated.

    The skeleton can be parsed from a a config and setting dictionary
    which contains all the information needed. The config dictionary
    can also be read into the Configuration class.

    The parsers can be found in the parser.py section of BOM analysis.
    """

    def __init__(self):
        """Parent class for the parsers used to create
        the skeletons.

        The skeleton is a dictionary of the parts that make
        up a hierarchy with each part as a unique key contained
        within it.

        Attributes
        ----------
        skeleton : dict
            The skeleton which will data will be parsed
            into."""
        self.skeleton = {}

    def __repr__(self):
        """Nice print of skeleton.

        Returns
        -------
        str
            A nicely printed dictionary with a readable.
            indentation.

        See Also
        --------
        pprint.pformat : Indents a dictionary to allow reading."""
        return pprint.pformat(self.skeleton, indent=4, width=1)

    def component_dictionary(
        self,
        component_ref: str,
        component_type: str,
        component_database: Dict[str, Dict],
        parameter_dictionary: dict,
    ) -> dict:
        """Creates a dictionary for a components or assembly.

        The component dictionary can be a simpler way of buildin a
        bill of materials component.

        Parameters
        ----------
        component_ref : str
            The reference for the component which will be created.
        component_type : str
            The type of component that will be created.
        component_database : dict
            The database of components which can be inheritted or child
            of the component type.
        parameter_dictionary : dict
            A dictionary of parameters where the keys are the params_name
            in the component_database.

        Returns
        -------
        dict
            A dictionary of the component, this is known as a skeleton.
        """
        self.skeleton = {}
        self.spine(component_ref, component_type, component_database)
        self.add_bones(component_database, parameter_dictionary)
        return self.skeleton

    def database(self, database_files: list) -> dict:
        """Method for loading and merging a list of database files.

        Parameters
        ----------
        database_files : list
            List of jsons that will be loaded into the returned object.

        Returns
        -------
        dict
            A dictionary of the merged jsons in the database_files.
        """
        return load_and_merge(database_files)

    def component_data(
        self,
        component_ref: str,
        component_type: str,
        component_database: Dict[str, Dict],
    ) -> Dict[str, Union[dict, str]]:
        """Extracts a component from a component_database
        with the type used as the key in the dict.

        Parameters
        ----------
        component_ref : str
            The reference for the component which will be created.
        component_type : str
            The type of component that will be created.
        component_database : dict
            The database of components which contains all the parts.

        Returns
        -------
        dict
            A dictionary of the component with the key as the ref.
        """
        data = copy.deepcopy(component_database[component_type])
        data["type"] = component_type
        data["ref"] = component_ref
        return data

    def merge_component_defined_with_skeleton(
        self, defined_in_component_database: dict, defined_on_child: dict
    ) -> dict:
        """Merges a dictionary of components defined on a child
        and within the parent["skeleton"].

        Information about a component can be defined on a child
        within the component dictionary or in a dictionary
        on the child key of a dictionary.

        Parameters
        ----------
        defined_in_component_database : dict
            Component dictionary within the component_database such as
            {breeder:{first:foo}}.
        defined_on_child : dict
            Child dictionary within a component_dictionary such as
            {blanket:{children:breeder:second:bar}}.

        Returns
        -------
        dict
            A merged dictionary for the component such as {breeder:{first:foo, second:bar}}.
        """
        if (
            "type" in defined_in_component_database
            and defined_in_component_database["type"] != defined_on_child["type"]
        ):
            return defined_on_child
        else:
            UpdateDict(defined_in_component_database, defined_on_child)
            return defined_in_component_database

    def spine(
        self,
        component_ref: str,
        component_type: str,
        component_database: Dict[str, Dict],
    ):
        """Creates the basic part of the skeleton by
        populating the children.

        Parameters
        ----------
        component_ref : str
            The reference for the component which will be created.
        component_type : str
            The type of component that will be created.
        component_database : dict
            The database of components which contains all the parts.
        """
        self.skeleton["_META"] = {"type": component_type, "ref": component_ref}
        self.children(
            self.skeleton, component_database, component_ref, {"type": component_type}
        )

    def children(
        self,
        skeleton: dict,
        component_database: Dict[str, Dict],
        reference: str,
        child_input: dict,
    ):
        """Imports the children into the skeleton.

        This function relies heavily on recursion
        to search down through all the children in order to
        populate the skeleton.

        Parameters
        ----------
        skeleton : dict
            A dictionary of the components within the
            hierarchy.
        component_database : dict
            Dictionary of all components.
        reference : str
            Unique reference for the part which is being assessed.
        child_input : dict
            Dictionary with type of the child, used to lookup component_database.

        Note
        ----
        Copy necessary when you have the same part ref
        used for different parts."""
        if reference not in skeleton:
            component_dict = self.component_data(
                reference, child_input["type"], component_database
            )
        else:
            component_dict = skeleton[reference]

        skeleton[reference] = self.merge_component_defined_with_skeleton(
            component_dict, child_input
        )
        if "children" in skeleton[reference]:
            children = skeleton[reference]["children"]
            for ref, child in children.items():
                self.children(skeleton, component_database, ref, child)

    def add_bones(self, parents: dict, parameters: dict):
        """Adds the more detailed information (the bones) to the skeletons.

        Parameters
        ----------
        parents : dict
            A dictionary of components which the items
            will be inherited.
        parameters : dict
            A dictionary which any params_name will be looked up
            in."""
        for name, component in self.skeleton.items():
            self.add_bone(component, parents, parameters)

    def add_bone(self, component: dict, parents: dict, parameters: dict):
        """Add a bone based on the basic information.

        Parameters
        ----------
        parents : dict
            A dictionary of components which the items
            will be inherited.
        parameters : dict
            A dictionary which any params_name will be looked up
            in.
        component : dict
            A dictionary for the component being assessed.

        Note
        ----
        Copy required as a new memory location for each item requred."""
        self.inherit(component, parents)
        self.all_params(component, copy.deepcopy(parameters))
        self.rm_inherits(component)

    def inherit(self, component: dict, parents: Dict[str, dict]):
        """Adds inherited information to the skeleton.

        This inherited information is important as there
        is it allows for some level of inheritance from
        within the jsons loaded i.e. a Brand of Car specified as
        an assembly in a supplied dictionary can inherit
        parameters, information and other data from Car
        if that is also supplied as a dictionary. It does
        this by looking for an inherits key.

        Parameters
        ----------
        component : dict
            The component which will be checked for an
            inherits key.
        parents : dict
            All the components which will be searched for
            for the values given by the inherits key."""
        parents = copy.deepcopy(parents)
        if isinstance(component, dict) and "inherits" in component:
            all_tup: Tuple = ()
            for string in component["inherits"]:
                self.inherit(parents[string], parents)
                all_tup += (parents[string],)
            UpdateDict(component, *all_tup)

    def rm_inherits(self, item: dict):
        """Having inherit left after the inheritance has
        taken place means running on an already populated skeleton is
        challenging, so it has to be replaced with inherited.

        Parameters
        ----------
        item : dict
            Contains the component from with the inheritance will
            be removed."""
        if isinstance(item, dict) and "inherits" in item:
            item["inherited"] = copy.deepcopy(item["inherits"])
            del item["inherits"]

    def all_params(self, component: dict, parameters: dict):
        """Adds parameters to the component.

        As with inheritance, params can be added by
        loading in from an external dictionary which are
        checked for values given by within the key param_str.
        When the params are loaded in the param_str is then deleted
        so that params are not loaded multiple times. The partucular
        parameter class (such as one with Pint integration) is also
        loaded in by the special string class_str.

        Parameters
        ----------
        component : dict
            The component which will be checked for an
            inherits key.
        parameters : dict
            All the parametrs which will be searched for
            for the values given by the parama_str key of
            the component.

        Note
        ----
        The switch from params to _params is to correctly parse
        for the updated components with params as a property.
        """
        self.add_default_param(component)

        if "params" in component:
            UpdateDict(component["_params"]["data"], component["params"]["data"])
            del component["params"]
        if "params_name" in component:
            for name in component["params_name"]:
                UpdateDict(component["_params"]["data"], parameters[name])
            del component["params_name"]

    def add_default_param(self, component: dict):
        """Adds the default parameter to the component dictionary.

        Parameters
        ----------
        component : dict
            The component dictionary which will have the default added to it.
        """
        if "_params" not in component:
            component["_params"] = {
                "data": {},
                "class_str": [BaseFramework._configuration._default_param_type],
            }


class ConfigParser(SkeletonParser):
    """Parses config to create basic skeleton.

    Attributes
    ----------
    defaults : dict, optional
        Default parameters which will be applied to the skeleton.
    paramters : dict, optional
        Any additional parameters defined by params_name.
    storage : dict, optional
        Any other attribututes to be added to a function
        where inherits is present.
    modules : dict, optional
        The modules which will be ran assessing the skeleton.
    """

    _config = {"parts": {"location": []}, "top": {}}

    def __init__(self, skeleton: dict, operate: bool = True):
        """Initialises the config parser.

        Parameters
        ----------
        skeleton : dict
            A predefined skeleton.
        operate : bool
            Whether everything should be parsed from the Config."""
        self.skeleton = skeleton
        self._config = {}
        if operate:
            self.update_config()
            self.create_skeleton()

    def update_config(self):
        """Updates the classes _config.

        This adds the Config class as a dictionary to the parser.
        Transforming this to a dictionary is used to
        align with children of this class.
        """
        config_dict = self._configuration.to_dict()
        if config_dict["_parts"] is not None:
            self._config["parts"] = config_dict["_parts"]
            assert (
                "location" in self._config["parts"]
            ), "location of files with parts not given"
        else:
            msg = "parts with a location must be supplied to the config to load from config"
            run_log.error(msg)
            raise ValueError(msg)
        if config_dict["_parameters"] is not None:
            self._config["parameters"] = config_dict["_parameters"]
            assert (
                "location" in self._config["parameters"]
            ), "location of files with parameters not given"
        else:
            msg = "parameters with a location must be supplied to the config to load from config"
            run_log.error(msg)
            raise ValueError(msg)

        UpdateDict(self._config, config_dict)

    def create_skeleton(self):
        """Parses config to create skeleton.

        This is done by first building the spine of
        the skeleton contianing all the parts in the
        hierarchy. Following htis, additional bones
        are added containing the parameters and inherited
        part information."""
        self.add_spine()
        self.add_bones_from_config(self._config)

    def add_spine(self):
        """Defines the components, the spine of the skeleton.

        This is performed by indentifying the top component
        in the hierarchy and then using recursion to add
        all the components below. The components are loaded from
        the parts file locations given in the config."""
        all_comp = self.database(self._config["parts"]["location"])
        top = self._config["top"]
        self.spine(top["ref"], top["type"], all_comp)

    def add_bones_from_config(self, *args):
        """Adds bones to the skelton such as the parameters
        from a config file.

        Parameters
        ----------
        args : tuple
            A tuple of the dictionary containing the data location,
            usually a config.
        """
        data = ["parts", "parameters"]
        parents, parameters = self.load_data_files(data, *args)
        self.add_bones(parents, parameters)

    def load_data_files(self, ordered_titles: Iterable, *args) -> tuple:
        """Loads the required data files.

        This is performed by checking the ordered titles against
        the dictionaries supplied in args. This means that
        the args could have multiple different file locations
        using the same key (such as a config and settings) and
        all would be loaded by this function.

        Parameters
        ----------
        ordered_titles : iterable
            A list or tuple of the ordered titles for
            files which will be loaded form the corresponding
            key in the supplied args.
        args : tuple
            A tuple of dicionaries which contain the locations
            of the files to be loaded where the ordered
            titles are the keys.

        Returns
        -------
        output : tuple
            A tuple of dictionarys of all the loaded data
            from the ordered titles, same length and order as
            ordered_titles.

        Note
        ----
        It was recommended not using lists unless necessary
        perhaps a concatenated string is better but
        could run into problems with string."""
        output: Tuple = ()
        for val in ordered_titles:
            path = []
            for arg in args:
                if val in arg and "location" in arg[val]:
                    path += arg[val]["location"]
            output += (load_and_merge(list(set(path))),)
        return output

    def add_default_param(self, component: dict):
        """Adds the default parameter to the component dictionary.

        Parameters
        ----------
        component : dict
            The component dictionary which will have the default added to it.
        """
        param_class = BaseFramework._configuration._default_param_type
        if "_params" not in component:
            component["_params"] = {"class_str": [param_class], "data": {}}
        elif "class_str" not in component["_params"]:
            component["_params"]["class_str"] = [param_class]


class SettingsParser(ConfigParser):
    """A class to parse a settings file and create a
    skeleton based on it and a base skeleton.
    Also checks the input."""

    def __init__(self, settings: dict, skeleton: dict, operate: bool = True):
        """initialises the settings parser.

        Parameters
        ----------
        settings : dict
            The settings which will be used to created the skeleton
            modifications.
        skeleton : dict
            A dictionary of the components within the
            hierarchy.
        operate : bool
            Whether the skeleton should be modified from the supplied
            settings file.
        """
        self._settings = settings
        self._config = {}
        self.update_config()
        self.skeleton = skeleton
        self.check_settings()
        self.create_vertebrae_pool()
        self.define_marrow()
        if operate:
            self.surgery()

    def create_vertebrae_pool(self):
        """Loads any vertebrae from a file,
        defaults to an empty dictionary.

        Attributes
        ----------
        vertebrae : dict
            The vertebrae that will make up
            the spint of the skeleton, basically all the
            parts."""
        (self.vertebrae,) = self.load_data_files(
            ["parts"], self._settings, self._config
        )

    def define_marrow(self):
        """Loads any vertebrae from a file,
        defaults to an empty dictionary.

        Attributes
        ----------
        defaults : dict
            Default parameter values which can be added to the skeleton.
        parameters : dict
            The parameters which can make up the skeleton.
        storage : dict
            Any additional storage which can be added.
        modules : dict
            Data on the modules which will be run on the skeleton."""
        (
            self.defaults,
            self.parameters,
            self.storage,
            self.modules,
        ) = self.load_data_files(
            ["defaults", "parameters", "storage", "modules"],
            self._settings,
            self._config,
        )

    def update_settings(self, settings: dict):
        """Updates the parser settings.

        Parameters
        ----------
        settings : dict
            The settings which will be used to created the skeleton
            modifications."""
        UpdateDict(self._settings, settings)
        self.check_settings()

    def check_settings(self):
        """Checks the user settings are ok and populates
        the settings with an empty type in the correct
        format when a key is missing."""
        if "part_changes" not in self._settings:
            self._settings["part_changes"] = {}
        if "top" not in self._settings:
            self._settings["top"] = self._config["top"]
        if "parts" not in self._settings:
            self._settings["parts"] = {"location": []}
        if "other_changes" not in self._settings:
            self._settings["other_changes"] = {}
        if "modules" not in self._settings:
            self._settings["modules"] = {"order": {}, "location": []}
        if "parameters" not in self._settings:
            self._settings["parameters"] = {"location": []}

    def surgery(self):
        """Performs surgery on the skeleton by rearranging
        the components, simplifying, populating based on
        the _settings.

        The analogy used to help undestanding continues from
        the skeleton. Initially, the settings may rearrange the
        vertebrae i.e. they may alter the hierarchy. Then the
        bones can be added like in the config file, followed
        by additional information (the marrow) such as particular
        data structures."""
        self.alter_vertebrae()
        if self._settings["part_changes"] != {}:
            run_log.warning(("rebuilding spine, all skeleton data will" "be wiped"))
            self.rebuild_spine(self.vertebrae)

        self.add_bones(self.vertebrae, self.parameters)
        self.add_marrow()

    def to_type_skeleton(self, skeleton: dict) -> dict:
        """Converts the skeleton to an input parts format
        with the keys swapped from the reference to the type.

        This is required so that data from a previously built
        skeleton can be used as input.

        Parameters
        ----------
        skeleton : dict
            A dictionary of the components within the
            hierarchy.

        Returns
        -------
        dict
            The skeleton with type as input."""
        type_skeleton = {data["type"]: data for data in skeleton.values()}
        for data in type_skeleton.values():
            if "ref" in data:
                del data["ref"]
        return type_skeleton

    def alter_vertebrae(self):
        """Alters the all component vertebrae which may or may not
        make up the skeleton.

        Initially updates the vertebrae with any changes, then
        adds the unchanged skeleton to the vertebrae. This allows
        the structure to be changed without all the inputs being
        supplied."""
        for name, val in self._settings["part_changes"].items():
            if name in self.skeleton:
                type_of_part = self.skeleton[name]["type"]
                if type_of_part in self.vertebrae:
                    base_vertebrae = self.vertebrae[type_of_part]
                    UpdateDict(base_vertebrae, val)

    def rebuild_spine(self, all_comp: dict):
        """Rebuilds the spine with only the required components.

        Parameters
        ----------
        all_comp : dict
            All the components which the rearranged spine can be
            added from."""
        top = self._settings["top"]
        if "type" not in top:
            top["type"] = self.skeleton[top["ref"]]["type"]
        self.skeleton.clear()
        self.children(self.skeleton, all_comp, top["ref"], {"type": top["type"]})

    def add_marrow(self):
        """Adds default parameters and makes changes to the system.

        This adds any non-structural changes and then introduces
        default parameters, materials, and data storage."""
        self.load_module_requirements(self.modules)
        for name, component in self.skeleton.items():
            self.load_defaults(name, component, self.defaults)
            if name in self._settings["other_changes"]:
                UpdateDict(component, self._settings["other_changes"][name], locked=[])

            if (
                "material" in component
                and "name" in component["material"]
                and "inherits" in component["material"]
            ):
                component["material"] = self.select_library(component["material"])
            self.load_storage(component, self.storage)

            self.all_params(component, self.parameters)
            # self.load_defaults(name, component, defaults)

    def load_defaults(self, ref: str, component: dict, defaults: dict):
        """Loads the defaults if they exist within the component.

        Parameters
        ----------
        ref : str
            The unique component reference.
        component : dict
            Dictionary with all component information.
        defaults : dict
            The defaults parameters to be added to the component."""
        if ref in defaults:
            default = {
                key: val for key, val in defaults[ref].items() if key != "_params"
            }
            params_dict = {
                key: val for key, val in defaults[ref].items() if key == "_params"
            }
            if "_params" in params_dict and "data" in params_dict["_params"]:
                params = params_dict["_params"]["data"]
            else:
                params = {}
            UpdateDict(component, default)
            if "_params" in component:
                for param, param_dict in params.items():
                    if (
                        param in component["_params"]["data"]
                        and component["_params"]["data"][param]["value"] is None
                    ):
                        UpdateDict(component["_params"]["data"][param], param_dict)

    def load_module_requirements(self, all_modules: dict):
        """Loads any data requirements a module has.

        This method is to allow the BOM Analysis Skeletons
        to be used by modules contained within the settings.
        It means that a module may require a particular component
        for assessment (such as a coolant) and that the skeleton can
        then be checked for it. Equally, if the part exists in the
        skeleton, parameter or storage requirements for the module
        can be added to the skeleton.

        Parameters
        ----------
        all_modules : dict
            All the modules, even the ones not in going to assessed
            i.e. the ones not included in the order.

        Raises
        ------
        ValueError
            Raised if the required module is not in the skeleton."""
        if all_modules != {}:
            for i_module in range(0, len(self._settings["modules"]["order"])):
                module_name = self._settings["modules"]["order"][str(i_module)]
                if "requirements" in all_modules[module_name]:
                    for name, change in all_modules[module_name][
                        "requirements"
                    ].items():
                        if name not in self.skeleton:
                            msg = f"{name} is not in the skeleton"
                            run_log.error(msg)
                            raise ValueError(msg)
                        else:
                            UpdateDict(self.skeleton[name], change)

    def load_storage(self, component: dict, storage: dict):
        """Loads the storage on a component.

        This allows additional storage types to be loaded
        into a component. As the skeleton is nothing more
        than a nested dictionary with particular, basic data
        types, the storage can be load in and will come with
        a class_str key if they are anything more than the
        basic data types.

        Parameters
        ----------
        component : dict
            Dictionary with all component information.
        storage : dict
            The storage dictionary to be loaded into the component."""
        new_params = []
        if "params_name" in component:
            new_params += component["params_name"]
        for name, bone in component.items():
            self.inherit(bone, storage)
            self.rm_inherits(bone)
            if isinstance(bone, dict) and "params_name" in bone:
                new_params += bone["params_name"]
                component[name] = {
                    key: val for key, val in bone.items() if key != "params_name"
                }

        component["params_name"] = new_params

    def select_library(self, material: dict):
        """Chooses materials library.

        Choses the material library for a given material string
        by searching each one to determine whether the material
        exists within in. The config also provides an order to the
        materials library, which will be search for and the loop
        stopped when the material is found.

        Parameters
        ----------
        material : str
            The material name.

        Raises
        ------
        ValueError
            Fails when the material does not exist in any of the
            databases."""
        material_selector = BaseFramework._configuration.materials
        material_database = material_selector.select_database(material["name"])
        database_dict = material_database.to_dict()
        UpdateDict(database_dict, material)
        material = database_dict
        return material
