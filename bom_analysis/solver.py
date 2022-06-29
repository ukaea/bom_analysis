from collections import OrderedDict
import copy
import time

from bom_analysis import ureg, run_log, Q_
from bom_analysis.base import BaseClass
from bom_analysis.utils import UpdateDict, load_and_merge, class_from_string


class Step:
    """The solver implemented in BOM Analysis is made up
    of a series of steps ran in linear order. Each step
    requires the class (not initialised) to be initialised,
    the method within the class that will be run plus and
    arguments or key word arguments. The solve function
    can then be run to execute the step."""

    def __init__(self, class_object: type, method_str: str, *args, **kwargs):
        """a class that defines a step in the solver.

        Parameters
        ----------
        class_object : type
            A class which will be initialises containing
            a mehtod to be solved.
        method_str : str
            The method within the class that will be ran.
        """
        self.class_object = class_object
        self.method_str = method_str
        self.args = args
        self.kwargs = kwargs

    @property
    def name(self):
        """The name of the class defined within the step.

        Returns
        -------
        str
            String for the name in step class.
        """
        return f"{self.class_object.__name__}.{self.method_str}"

    def solve(self):
        """Solves the class within the step class and
        records the time taken for the step to solve in the
        run log.
        """
        start = time.time()
        instance = self.class_object()
        method = getattr(instance, self.method_str)
        method(*self.args, **self.kwargs)
        end = time.time()
        run_log.info(
            (
                f"\n###########################"
                f"\n{self.name} took {end-start} to run"
                f"\n###########################\n"
            )
        )

    def to_dict(self):
        """Returns a deifnition of the step to a dictionary.

        Returns
        -------
        dict
            A dictionary defining the step.
        """
        return dict(
            class_str=f"{self.class_object.__module__}.{self.class_object.__name__}",
            run=self.method_str,
            args=self.arg_to_str_list(),
            kwargs=self.kwarg_to_str_dict(),
        )

    def arg_to_str_list(self):
        """Converts the input arguements to a
        list with any components being written as references
        instead of the object.

        Returns
        -------
        list
            A list of arguments.
        """
        arg_list = []
        for arg in [*self.args]:
            if hasattr(arg, "_ref"):
                arg_list.append(arg.ref)
            else:
                arg_list.append(arg)
        return arg_list

    def kwarg_to_str_dict(self):
        """Converts the input keywords to a
        list with any components being written as references
        instead of the object.

        Returns
        -------
        dict
            A list of dictionary of key words.
        """
        kwarg_dict = {}
        for key, val in {**self.kwargs}.items():
            if hasattr(val, "_ref"):
                kwarg_dict[key] = val.ref
            else:
                kwarg_dict[key] = val
        return kwarg_dict


class Solver(BaseClass):
    """The solver contains an ordered dictionary which should be
    made up of the steps that the analysis will go through. It can be
    populated manually or build from a settings file.

    As with the engineering objects the solver can be written
    to a dictionary using the same method names."""

    def __init__(self):
        """Initialises and defines the ordered dict.

        See Also
        --------
        collections.OrderedDict : A dictionary with the order of the run."""
        self.run = OrderedDict()

    def build_from_settings(self, settings, assembly):
        """Builds the ordered dictionary by taking the required modules
        from the settings and defining json and building a class from string.

        If the module settings call for a particular reference, and that
        reference is in the flattened assembly the solver will be provided
        with that part of the assembly. The solver initialises the module
        but does not run any functions outside the __init__."""
        mod_settings = copy.deepcopy(settings["modules"])
        all_modules = load_and_merge(mod_settings["location"])
        flat = assembly.flatten()
        for i_module in range(0, len(mod_settings["order"])):
            module_name = mod_settings["order"][str(i_module)]
            module = all_modules[module_name]
            if module_name in mod_settings:
                UpdateDict(module, mod_settings[module_name])
            self.update_args(module, flat)
            self.update_kwargs(module, flat)
            step = Step(
                class_from_string(module["class_str"]),
                module["run"],
                *module["args"],
                **module["kwargs"],
            )
            self.run[module_name] = step

    def build_from_step_list(self, step_list: list):
        """Builds a run array from a list of steps.

        Parameters
        ----------
        step_list : list
            List of Step classes that will be ran in order.
        """
        for step in step_list:
            self.run[step.name] = step

    def solve(self):
        """Solves the functions in the ordered dict."""
        for step in self.run.values():
            step.solve()

    def to_dict(self, exclusions=[]):
        """Outputs the full dictionary of the
        solver Steps.

        Parameters
        ----------
        exclusions : list, optional
            Anything to be excluded from the dictionary by default [].

        Returns
        -------
        dict
            The dictionary representing the sovler.
        """
        step_details = {name: step.to_dict() for name, step in self.run.items()}
        order = {str(i_step): name for i_step, name in enumerate(self.run.keys())}
        return dict(order=order, details=step_details)

    def update_kwargs(self, module, flat):
        """Updates any kwargs with the component if
        exists in flat.

        Parameters
        ----------
        flat : dict
            Flattened components in BoM.
        module : dict
            Information about the module."""
        if "kwargs" in module:
            module["kwargs"] = self.replace_with_comp(module["kwargs"], flat)
        else:
            module["kwargs"] = {}

    def update_args(self, module, flat):
        """Updates any args with the component if
        exists in flat.

        Parameters
        ----------
        flat : dict
            Flattened components in BoM.
        module : dict
            Information about the module."""
        if "args" in module:
            module["args"] = self.replace_with_comp(module["args"], flat)

        else:
            module["args"] = ()

    def replace_with_comp(self, item, flat):
        """Replaces a string with a component in
        the args/kwargs to allow dictionary/list to be supplied.

        Parameters
        ----------
        flat : dict
            Flattened components in BoM.
        item : type
            An instance which might contain the reference of a component.

        Returns
        -------
        type
            An instance with the reference replaced with the component
            the type of which is the same as the input."""
        if isinstance(item, list):
            new_list = []
            for element in item:
                new_list.append(self.replace_with_comp(element, flat))
            return new_list
        elif isinstance(item, dict):
            new_dict = {}
            for key, element in item.items():
                new_dict[key] = self.replace_with_comp(element, flat)
            return new_dict
        elif isinstance(item, tuple):
            new_item = ()
            for element in item:
                new_item += (self.replace_with_comp(element, flat),)
            return new_item
        else:
            if item in flat:
                item = flat[item]
            return item
