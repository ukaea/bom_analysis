from pathlib import Path
from typing import Union

from bom_analysis import run_log, BaseFramework
from bom_analysis.bom import Assembly, EngineeringObject
import bom_analysis.parsers as ps
from bom_analysis.solver import Solver


class Framework(BaseFramework):
    """The framework offers an automated way of populating configurations,
    translators, settings, and parsing skeletons uting dictionaries.
    Following poplulation of the various different required information
    it can then getnerate the bill of materials and solve the analysis
    workflow.

    The solver and the configuration are stored as class variables."""

    _solver = Solver

    def __init__(
        self, config_path: Union[str, Path, None] = None, config_dict: dict = {}
    ):
        """initialisation for the framework.

        Parameters
        ----------
        config_dict : dict
            A dictionary containing the config file.
        config_path : str
            A string containing the config file location."""
        self.initialise_cross_class(config_path=config_path, config_dict=config_dict)

        self.skeleton = {}
        ps.ConfigParser(self.skeleton)

    @classmethod
    def initialise_cross_class(
        cls,
        login: bool = False,
        config_path: Union[str, Path, None] = None,
        config_dict: dict = {},
    ):
        """Initialises the classes that supply
        information and funcitonality across the
        bom_analysis.

        Parameters
        ----------
        loggin : bool, optional
            Login details required.
        config_dict : dict, optional
            A dictionary containing the config file.
        config_path : str, optional
            A string containing the config file location."""
        if config_dict == {} and config_path == "":
            msg = "framework must have either a path to config dict or dict"
            run_log.warning(msg)
        else:
            super()._configuration.define_config(
                config_path=config_path, config_dict=config_dict
            )

    def settings(self) -> dict:
        """Return a dictionary of the settings that have been used
        in the solver.

        Returns
        -------
        dict
            A dicitionary containing all the solver settings.
        """
        return dict(modules=self._solver.to_dict())

    @classmethod
    def reader(
        cls,
        skeleton: dict,
        top: Union[str, None] = None,
        settings: str = {},
        config_path: Union[str, Path, None] = None,
        config_dict: dict = {},
    ) -> EngineeringObject:
        """Returns a class representing the populated bill of materials
        by parsing information from loaded from the config and settings.

        This class reads defines teh config, and uses the settings
        to take a skeleton and populate bill of materials object.
        The skeleton can be supplied if a modification on an existing
        skeleton is requried.

        Parameters
        ----------
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object.
        top : str, optional
            Reference of the instance sitting at the top of the
            hierarchy.
        settings : dict, optional
            A dictionary of the settings for framework.
        config_dict : dict, optional
            A dictionary containing the config file.
        config_path : str, optional
            A string containing the config file location.

        Returns
        -------
        assembly : bom_analysis instance
            A populated assembly from framework.bom.

        See Also
        --------
        framework.bom.Assembly : An engineering object with a sub assembly.
        """
        if config_path is not None or config_dict != {}:
            super()._configuration.define_config(
                config_path=config_path, config_dict=config_dict
            )

        if top is None and settings == {} and not hasattr(cls._configuration, "top"):
            raise ValueError(
                "top level must be suplined directly or in settings/config"
            )
        elif top is not None:
            if "top" in settings:
                settings["top"]["ref"] = top
            else:
                settings["top"] = {"ref": top}

        ps.SettingsParser(settings, skeleton)
        assembly = Assembly()

        assembly.from_dict(skeleton, ref=settings["top"]["ref"])
        return assembly

    @classmethod
    def load(cls, top: str, skeleton: dict) -> EngineeringObject:
        """Simple load of a skeleton to BoM structure.

        This loads the skeleton but does not load the
        settings or config.

        Parameters
        ----------
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object.
        top : str, optional
            Reference of the instance sitting at the top of the
            hierarchy.

        Returns
        -------
        Assembly
            A populated assembly from framework.bom.
        """
        assembly = Assembly()
        assembly.from_dict(skeleton, ref=top)
        return assembly

    @classmethod
    def solver(
        cls, settings: dict = {}, assembly: Union[EngineeringObject, None] = None
    ) -> Solver:
        """Creates a solver based on the settings.

        Creates a solver object from the settings (which
        define the modules that will be run) and the
        assembly.

        Parameters
        ----------
        assembly : bom_analysis instance
            A populated assembly from framework.bom.
        settings : dict
            The settings for the framework containing the modules
            that will be run.

        Returns
        -------
        ordered_run : type
            A solver object which has assigned parts of the
            assembly to solvers and defined an order to
            run in.

        See Also
        --------
        framework.solver : A solver object.
        """
        ordered_run = cls._solver()
        if settings != {}:
            ordered_run.build_from_settings(settings, assembly)
        return ordered_run
