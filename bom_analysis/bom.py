from collections import Counter
import copy
import weakref

import numpy as np
import pandas as pd
import treelib

from bom_analysis import BaseFramework, run_log
from bom_analysis.base import BaseClass
from bom_analysis.materials import MaterialData
from bom_analysis.parameters import ParameterFrame
from bom_analysis.utils import UpdateDict, class_factory, class_from_string


class NonUniqueComponentReference(Exception):
    """Error for when there is a non-unique reference
    to the required coomponents i.e. two components within the
    same body that have the same assignment.
    """

    pass


class EngineeringObject(BaseClass):
    """The Engineering Object is a parent class for parts within the bill of
    materials. It contains key variables and methods which allow the
    bill of materials to function."""

    def __init__(self, ref: str = None, assignment: str = None):
        """
        The engineering object forms the parent for
        all components within the bill of materials and is defined by
        having a number of required attributes.

        All engineering objects should have a unique reference or
        part number (ref). The unique nature of the reference can be
        checked and an error will be raised if there is another component
        in an assembly that has the same reference but is not the same object.

        Parameters
        ----------
        ref : str, optional
            the reference for the engineering object, must be unique.

        Attributes
        ----------
        _ref : str, private
            The private variable for the reference.
        _assignment : np.ndarray, private
            A array for adding assignments to a component.
        _params : None, private
            The private assigment dedicated to a parameter frame assignment.
        """
        self._ref = None
        self._assignment = np.array([], dtype=str)
        self._params = None
        self.ref = ref
        self.add_default_params()
        try:
            if assignment is not None:
                self.assignment = assignment
        except ValueError:
            self.assignment = assignment

    def __repr__(self):
        """
        Magic method for creating a string to be printed.

        Prints the class name, component reference and identifier.

        Returns
        -------
        str
            String for __repr__.
        """
        return (
            f"\n{self.__class__.__name__}.ref = {self.ref}"
            f"\nidentity = {hex(id(self))}"
        )

    def __str__(self):
        """Magic method for displaying the engineering object as a string.

        Displays the class name and reference.

        Returns
        -------
        str
            String for __str__."""
        return f"{self.__class__.__name__} " f"with reference {self.ref}"

    @property
    def ref(self):
        """
        Referencing is one of the most important concepts 
        in BOM analyis. Information about how the ref works can be 
        found in the
        `documentation <https://bom-analysis.readthedocs.io/en/latest/Structure_of_Hierarchy.html#reference-the-most-important-thing-to-remember>`_.       

        """
        return self._ref

    @ref.setter
    def ref(self, value: str):
        """Setter for _ref private variable.

        Parameters
        ----------
        value : str
            The string value to be assigned to the reference.
        """
        self._ref = value

    @property
    def assembly(self):
        """Bolean as to whether it has sub components.

        A sub assembly is assumed to differentiate itself
        from a component on whether or not it has the
        _sub_assembly attribute.

        Returns
        -------
        boolean
            Boolean on whether it has the _sub_assembly attribute."""
        if hasattr(self, "_sub_assembly"):
            return True
        else:
            return False

    @property
    def assignment(self):
        """
        Information about how the assignment works can be found in the
        `documentation <https://bom-analysis.readthedocs.io/en/latest/Variables.html#assignment>`_.
        """
        return self._assignment

    @assignment.setter
    def assignment(self, value: str = None):
        """An engineering object can be assigned values
        such as 'Blanket' or 'Layer_2' or 'Yellow' via this
        setter.

        The aim of the assignment is to provide a list of strings
        that can be used in the calculation. For example, an engineering
        object may always want to be assigned the color "Yellow". The setter
        only returns unique assignments.

        Parameters
        ----------
        value : str, optional
            A string which will be added to the assignment, by default None.
        """
        new_assignment = np.append(self._assignment, value)
        self._assignment = np.unique(new_assignment)

    @property
    def params(self):
        """The property which represents the parameters
        of the engineering object.

        The parameters hold specific variables of an engineering
        object in a ParameterFrame class to allow for easy
        reference, display, and access to key engineering variables
        such as mass or volume.

        Returns
        -------
        ParameterFrame
            The parameterframe of the parameters.
        """
        return self._params

    @params.setter
    def params(self, value: ParameterFrame):
        """The setter for the parameter frame.

        Parameters
        ----------
        value : ParameterFrame
            The parameter to be assigned to the _params.
        """
        self._params = value

    @property
    def material(self):
        """The material property of the engineering object.

        The material is key to the bill of materials. Components
        have specific materials such as eurofer or helium while
        assemblies may have homogenised materials for neutronics
        assessment.

        Returns
        -------
        MaterialData
            A class for the materials."""
        return self._material

    @material.setter
    def material(self, value: MaterialData):
        """Setter for the material of the component.

        Parameters
        ----------
        value : MaterialData
            The material data to be assigned to the _material.
        """
        self._material = value

    def add_default_params(self):
        """
        Adds a default parameter to the
        engineering object.

        The default parameter is taken from the Configuration class
        in the BaseFramework. An unmodified BOM Analysis will
        default to a PintFrame which has native Pint units.
        """
        self.params = class_from_string(
            BaseFramework._configuration._default_param_type
        )()

    def add_default_material(self):
        """
        Adds a material class to the
        engineering object.

        Similar to adding the default parameter, this method
        adds a default material class to the engineering object. The
        default is a dummy database that does not have any data extraction
        capibility.
        """
        self.material = class_from_string(
            BaseFramework._configuration._default_material
        )()

    def assign_all_materials(self):
        """Loops through all engineering objects nested within the engineering
        object and assigns materials databases where possible.
        """
        flat = self.flatten()
        for comp in flat.values():
            comp.assign_materials_database()

    def assign_materials_database(self):
        """Assigns a new material database to the engineering object
        based on the name of material and priority of databases.

        The configuration contains a materials selector which
        can be searched through for a particular material string
        such as Helium. If this selector has been initialised and populated correctly
        then a new database with the previous temperature and pressure assignment will
        be created.
        """
        if hasattr(self, "material") and self.material.mat is not None:
            new_database = BaseFramework._configuration.materials.select_database(
                self.material.mat
            )
            new_database.reftemp = self.material.reftemp
            new_database.pressure = self.material.pressure
            self.material = new_database

    def add_class(self, class_name, class_data):
        """Adds a class from data to the class instance.

        This function utilises the class factory in the framework.utils
        to create a new class with type.

        Parameters
        ----------
        class_name : string
            The name of the class.
        class_data : dict
            The data that will be added to a new class."""
        new_sub_class = class_factory(class_name, class_data["class_str"], class_data)
        if hasattr(new_sub_class, "from_dict") and not isinstance(
            new_sub_class, pd.DataFrame
        ):
            new_sub_class.from_dict(class_data)
        setattr(self, class_name, new_sub_class)

    def from_dict(self, skeleton, ref=None):
        """Builds the part from the json.

        Parameters
        ----------
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object.
        ref : str
            From_dict is used recursively, if supplied a reference
            it looks up the skeleton top level keys with the ref.__base__."""
        if ref is not None:
            self.ref = ref
        elif self.ref is None and "_META" in skeleton:
            self.ref = skeleton["_META"]["ref"]
        if hasattr(self, "_ref") or hasattr(self, "ref"):
            super().from_dict(skeleton[self.ref])
        for name, val in skeleton[self.ref].items():

            if type(val) == dict and "class_str" in val:
                self.add_class(name, val)

    def check_duplicate(self, component_1, component_2):
        """Check whether a two components adhere to the
        bill of materials rules on the names of _ref.

        Within a bill of materials components must have
        different references if they are different. If a
        component is used in a different assembly in the bill
        of materials it can still have the same reference if
        the object is the same. This is checked by this method.

        Parameters
        ----------
        component_1 : EngineeringObject
            First Component for comparison.
        component_2 : EngineeringObject
            Second Component for comparison.

        Raises
        ------
        NonUniqueComponentReference
            If the component has a different id and the same reference.
        """
        if component_1.ref == component_2.ref and id(component_1) != id(component_2):
            msg = f"{component_1.ref} has already been used but instances are not the same"
            run_log.error(msg)
            raise NonUniqueComponentReference(msg)

    def flatten(self, flat=None):
        """Returns a flat dict of components.

        Parameters
        ----------
        flat : dict
            A pre build dictionary, used when flatten is
            operated recursively.

        Returns
        -------
        flat : dict
            A updated dictionary with the engineering objects
            flatteded self."""
        if flat is None:
            flat = {}
        if self.ref in flat:
            self.check_duplicate(self, flat[self.ref])
        else:
            flat[self.ref] = self
        return flat

    def lookup(self, *args):
        """Searches the sub_assembly for chosen data.

        This fuction looks up the attributes within an
        engineering object where the attributes are supplied
        as arguments.

        Parameters
        ----------
        args : str, optional
            Parameter strings that will be extracted.

        Returns
        -------
        lookup : dict
            A dictionary of the lookup values with the
            first key as the engineering object reference.

        Note
        ----
        This allows for part consistancy to be checked
        i.e. that part references are unique to a component
        (there can still be multiple components using the
        same reference)."""
        param_dict = {}
        for arg in args:
            param_dict[arg] = getattr(self, arg, None)
        return {self.ref: param_dict}

    def lookup_params(self, *args):
        """Searches the sub_assembly for chosen data.

        Parameters
        ----------
        args : str
            Parameter strings that will be extracted.

        Returns
        -------
        dict
            A dictionary of the component and any lookup
            parameters.

        Notes
        -----
        This allows for part consistancy to be checked
        i.e. that part references are unique to a component
        (there can still be multiple components using the
        same reference)."""
        param_dict = {}
        for arg in args:
            param_dict[arg] = getattr(self.params, arg, None)
        return {self.ref: param_dict}

    def copy_part(self):
        """Creates a copy of the component.

        For the complex classess, using copy.deepcopy(x)
        did not work, therefore a in-built method was created.
        This function works by converting the class with to_dict
        copying that and then using the class factory to recreate
        it.

        Returns
        -------
        new_class : instance
            Copy of the part."""
        skeleton = self.to_dict()
        new_dict = copy.deepcopy(skeleton)
        new_class = self.create_class_from_data(self.ref, new_dict, self_copied=True)
        return new_class

    def create_class_from_data(self, ref, skeleton, self_copied=False):
        """To correctly create a class from data more some additional
        changes must me made in addition to loading in the class
        and then using from_dict. This is to allow the master registers
        to be merged so that duplicate components are not created (and
        fail due to not being unique).

        Parameters
        ----------
        ref : str
            The reference for the engineering object, must be unique.
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object.
        self_copied : boolean
            A boolean on whether the instance is being copied. If an instance
            is being copied then merging the master registers means that a
            true copy is not formed (as it uses the weak ref of the register).

        Returns
        -------
        new_class
            An initialised copy of the object.
        """
        new_data = skeleton[ref]
        new_class = class_factory(ref, new_data["class_str"], {"ref": ref})
        new_class.ref = ref
        if new_class.assembly:
            new_class.master_register = {new_class.ref: weakref.ref(new_class)}
            if not self_copied:
                new_class.master_register.update(self.master_register)
        new_class.from_dict(skeleton)
        return new_class

    def add_defaults(self, defaults: dict):
        """Calls the add_defaults method in the
        ParameterFrame to populate it from a dictionary.

        The dictionary based parameter population allows for
        a full skeleton format {<ref>:{'params':{'data':{'mass':{'value':10}}}}}
        or just {<ref>:{'mass':10}}.

        Parameters
        ----------
        defaults : dict
            The dictionary of defaults that will be added to the EngineeringObject.
        """
        flat = self.flatten()
        default_copy = copy.deepcopy(defaults)
        for key, val in default_copy.items():
            if key in flat:
                if "material" in val:
                    flat[key].material.add_defaults(val["material"])
                    del val["material"]
                flat[key].params.from_dict(val)


class Component(EngineeringObject):
    """
    Information about how the Component works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Structure_of_Hierarchy.html#component-the-lowest-level>`_.
    """

    def __init__(self, ref: str = None, material: str = None, assignment: str = None):
        """A component engineering object. Adds a default
        material class for the component.

        The materials are default by component as they a
        act similar to a material specification.

        Parameters
        ----------
        ref : str, optional
            The reference for the engineering object, must be unique.
        """
        super().__init__(ref=ref, assignment=assignment)
        self.add_default_material()
        if material is not None:
            self.material.mat = material

    def to_dict(self, exclusions: list = []):
        """Converts the component to a dictionary.

        This method uses super to call the to_dict from
        the BaseClass.

        Parameters
        ----------
        exclusions : list, optional
            A list of attibutes that will be excluded
            from the conversion to the dictionary.

        Returns
        -------
        dict
            A dictionary containing all the component
            information."""
        component_dump = super().to_dict(exclusions=exclusions)
        if self.ref in component_dump.keys():
            return component_dump
        else:
            return {self.ref: component_dump}

    def hierarchy(self, tree=None, parent_node=None):
        """Used to create a hierarch of a BOM.

        This is a basic return due so that the
        main hierarchy of an assembly does not
        need to distinguish between components or
        assemblies.

        Parameters
        ----------
        tree : treelib instance, optional
            A hierachy treelib instance.

        Returns
        -------
        tree : treelib instance
            A hierachy treelib instance."""
        tree.create_node(tag=self.ref, parent=parent_node.identifier)
        return tree


class SubAssembly(dict):
    """Dictionary with an export.

    Note
    ----
    This maybe depricated as it can be replaced
    with a dictionary."""


class Assembly(EngineeringObject):
    """
    Information about how the Assembly works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Structure_of_Hierarchy.html#assembly-made-of-of-components-and-assemblies>`_.
    """

    def __init__(self, ref: str = None, assignment: str = None):
        """The assembly is a child of the engineering object
        and adds functionality to have a set of sub components
        and assemblies.

        The assembly forms the basis of the BOM Analysis and
        manages the sub assembly with getattr defaulting to
        taking items out of the sub assembly. A master register
        is a dicitonary of weak references to components and is
        designed to track the used references to check that the
        rules around the use of refererences (i.e. unique) are met.

        Parameters
        ----------
        ref : str, optional
            The reference for the engineering object, must be unique.

        Attributes
        ----------
        _sub_assembly : SubAssembly
            The class which stores all the componenets in that sit
            below this assemby class.
        _part_count : Counter
            A counter for the references within the sub assembly.
        master_register : dict
            A dictionary of with the references of all components
            in the connected assembly (above and below) and weakrefs
            to their instances.
        """
        super().__init__(ref=ref, assignment=assignment)
        self._sub_assembly = SubAssembly()
        self._part_count = Counter()
        self.master_register = {ref: weakref.ref(self)}

    def __getitem__(self, item_name):
        """Gets improves the ease of pulling an item from
        the sub_assembly. Allows assembly[item_string] to
        return item within sub_assembly.

        Parameters
        ----------
        item_name : str
            The name of an engineering object in the subassembly
            or attribute.

        Returns
        -------
        attribute
            An attribute from sub assembly if exists or __dict__
            if it does not.
        """
        if item_name in self._sub_assembly:
            return self._sub_assembly[item_name]
        elif item_name in self.__dict__:
            return self.__dict__[item_name]
        else:
            raise AttributeError("Attribute does not exist")

    def __getattr__(self, item_name):
        """Gets improves the ease of pulling an item from
        the sub_assembly. Allows assembly[item_string] to
        return item within sub_assembly.

        Parameters
        ----------
        item_name : str
            The item name which will be used to
            access the sub assembly first and
            the __dict__ after."""
        if item_name in self._sub_assembly:
            return self._sub_assembly[item_name]
        elif item_name in self.__dict__:
            return self.__dict__[item_name]
        else:
            raise AttributeError(f"Attribute [{item_name}]does not exist in {self.ref}")

    def __len__(self):
        """Allows the len to be used on the _sub_assembly.

        Returns
        -------
        int
            Length of the _sub_assembly."""
        return len(self._sub_assembly)

    def __iter__(self):
        """Allows the assembly object to be iterated on to return the
        sub_assembly items.

        Returns
        -------
        iterable
            An iterable for the _sub_assembly."""
        return iter(self._sub_assembly.values())

    def __repr__(self):
        """Print magic method.

        Returns
        -------
        str
            String for printing continaing the engineering
            object.__repr__ plus the _sub_assembly keys.

        Note
        ----
        The hierarchy may not show in jupyter as the
        tree class does not have a __repr__ and instead calls print."""
        return f"{super().__repr__()}\nhierarchy = {self.plot_hierarchy()}"

    def to_dict(self, exclusions: list = ["master_register", "_sub_assembly"]):
        """Converts the component to a dictionary.

        This method uses super to call the to_dict from
        the BaseClass.

        Parameters
        ----------
        exclusions : list, optional
            A list of attibutes that will be excluded
            from the conversion to the dictionary.

        Returns
        -------
        dict
            A dictionary containing all the component
            information."""
        this_component_dump = super().to_dict(exclusions=exclusions)
        dump = {self._ref: this_component_dump}
        this_component_dump["children"] = {}
        for ref, child in self._sub_assembly.items():
            component_dump = child.to_dict(exclusions=exclusions)
            this_component_dump["children"].update(
                self.sub_assembly_to_child(ref, component_dump[ref])
            )
            for key, val in component_dump.items():
                if key not in dump:
                    UpdateDict(dump, {key: val})
        return dump

    def sub_assembly_to_child(self, ref: str, child_dictionary: dict):
        """Converts a sub assembly to a child that can
        be written to a skeleton.

        As a skeleton is flat (no hierarchy) defining a
        sub assembly on a component within a dumped
        dictionary is not appropriate as it would (by definition)
        be very nested. To avoid this the children are used
        to represent the sub assembly, containing the child
        reference and a type (if exists).

        Parameters
        -----------
        ref : str
            The reference of the child.
        child_dictionary :
            The childs skeleton.

        Returns
        -------
        dict
            A dictionary containing a the reference
            and a type of that reference.

        Note
        ----
        The type of component only usually exists if it the skeleton
        has been parsed together."""
        if "type" in child_dictionary:
            return {ref: {"type": child_dictionary["type"]}}
        else:
            return {ref: {"type": ref}}

    def from_dict(self, skeleton, ref=None):
        """Checks the assembly for children.

        This function uses super to call the
        BaseClass from_dict and then adds any children
        it the instance has.

        Parameters
        ----------
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object.
        ref : str
            From_dict is used recursively, if supplied a reference
            it looks up the skeleton top level keys with the ref.__base__."""
        super().from_dict(skeleton, ref=ref)
        self._part_count.clear()
        if hasattr(self, "children"):
            self.add_children(skeleton)

    def add_children(self, skeleton):
        """Creates and adds to _sub_assembly.

        Uses the class factory and recursion to
        add all components in the below it in the hierarchy.
        This means that, if this instance is a car, the wheel
        sub assembly instance would be created, as well as the
        hub cap sub assembly of the wheel.

        Parameters
        ----------
        skeleton : dict
            A dictionary containing all the information about an
            engineering object. The first level keys are the names
            of the parts which make up the engineering object."""
        children = getattr(self, "children")
        for child in children:
            if child in self.master_register:
                child_class = self.master_register[child]()
            else:
                child_class = self.create_class_from_data(child, skeleton)
            self.add_component(child_class)

    def component_from_string(self, string):
        """Returns a component within the nested sub assembly
        based on a . delimited string.

        Parameters
        ----------
        string : str
            A . delimited string which gives the hierarchical
            path to the component.

        Returns
        -------
        component : Assembly instance
            A populated assembly instance."""
        component_list = string.split(".")
        if (
            component_list[0] == self.ref
            and component_list[0] not in self._sub_assembly
        ):
            component_list = component_list[1::]
        component = self
        for ref in component_list:
            component = getattr(component, ref)
        return component

    def flatten(self, flat=None):
        """Returns a flat dict of components.

        Flattening the components is very useful as it
        allows an object to be called by its reference
        no matter where it sits in the hierarchy.

        Parameters
        ----------
        flat : dict, optional
            A previously defined flattened dictionary
            to allow for recursion.

        Returns
        -------
        flat : dict
            A dictionary containing all the components in the
            sub assembly where the keys are the component reference.

        Note
        ----
        Previous releases fuction used flat={}
        but ran into `this <https://stackoverflow.com/questions/6794285/python-function-remembering-earlier-argument-kwargs>`_ 
        problem.
        """
        flat = super().flatten(flat=flat)
        for comp in self._sub_assembly.values():
            comp.flatten(flat=flat)
        return flat

    def lookup(self, *args):
        """
        Searches the sub_assembly for chosen data.

        Parameters
        ----------
        args : str
            Parameter strings that will be extracted.

        Notes
        -----
        This allows for part consistancy to be checked
        i.e. that part references are unique to a component
        (there can still be multiple components using the
        same reference).
        """
        params = super().lookup(*args)
        for part in self._sub_assembly.values():
            params.update(part.lookup(*args))
        return params

    def lookup_params(self, *args):
        """Searches the sub_assembly for chosen data.

        Parameters
        ----------
        args : str
            Parameter strings that will be extracted.

        Note
        ----
        This allows for part consistancy to be checked
        i.e. that part references are unique to a component
        (there can still be multiple components using the
        same reference)."""
        params = super().lookup_params(*args)
        for part in self._sub_assembly.values():
            params.update(part.lookup_params(*args))
        return params

    def add_component(self, component, ref=None):
        """Add components to the _sub_assembly, meant to allow
        for non-skeleton assembly creation.

        Parameters
        ----------
        component : instance
            An object to be added to the sub assembly.
        ref : str, optional
            A reference for the component to be added."""
        if component.ref is None:
            if ref is None:
                raise ValueError("ref must be supplied or a component attribute")
            else:
                component.ref = ref
        self.add_to_register(component)
        self._part_count[component.ref] += 1
        self._sub_assembly[component.ref] = component
        if component.assembly:
            self.merge_register()

    def remove_component(self, component_ref: str):
        """removes a component from a sub assembly.

        To remove a component from the sub assembly is
        important as the part count and master register
        can change.

        The master register on assemblies above this component
        are not updated (as there is no link up the tree),
        instead, self.update_all_sub_assemblies() should be
        used to rebuild the register on the top level component.

        Parameters
        ----------
        component_ref : str
            The unique reference of teh component to be removed.
        """
        if self._part_count[component_ref] > 1:
            self._part_count[component_ref] -= 1
        elif self._part_count[component_ref] == 1:
            del self._sub_assembly[component_ref]
            del self._part_count[component_ref]
            self.update_all_sub_asseblies()
        else:
            run_log.warning(
                (
                    f"trying to remove a component <{component_ref}> that does not"
                    f" exist in the assembly <{self.ref}>"
                )
            )

    @property
    def part_count(self):
        return self._part_count

    def count_ref(self, reference):
        """Counts the number of times a reference
        has been added to the sub-assembly.

        This allows multiple part numbers to be referencen
        within the same assembly. As BOM analysis is for analysis
        components with different attributes (such as temperature)
        will need to be considered carefully.

        Parameters
        ----------
        reference : str
            The reference for the component that will be checked for
            in the counter.

        Returns
        -------
        int
            The number of this component that has been added to the
            assembly.
        """
        return self.part_count[reference]

    def add_components(self, components: np.array = None):
        """Add components to the _sub_assembly, meant to allow
        for non-skeleton assembly creation.

        Parameters
        ----------
        components : np.ndarray
            An object to be added to the sub assembly.
        """
        for component in components:
            self.add_component(component)

    def add_to_register(self, component: EngineeringObject):
        """Aims to add a component to a master register if the
        componnet is not already within the master register.

        If the component already exists within the register
        it is checked against the rules of the reference. If it does
        not, a weak reference to the component is added to the
        masterregister.

        Parameters
        ----------
        component : EngineeringObject
            The component or assembly which is to be
            added to the master register.
        """
        if component.ref in self.master_register:
            self.check_duplicate(component, self.master_register[component.ref]())

        else:
            self.master_register[component.ref] = weakref.ref(component)

    def merge_register(self):
        """Merges to registers together from an assembly.

        In order to have a master register that contains
        all component references throughout the entire
        assembly (not just at the level of self) the master
        registers are merged. flatten() is used to do this and
        also contains a check duplicate check. There is a
        compulational overhead in calling flatten each time
        but flatten is relatively quick to run.
        """
        flat = self.flatten()
        for comp in flat.values():
            if comp.assembly:
                self.master_register.update(comp.master_register)
                comp.master_register = self.master_register

    def hierarchy(self, tree=None, parent_node=None):
        """Creates a nice graph showing the hierachy.

        Parameters
        ----------
        tree : treelib instance, optional
            A treelib instance which may contain nodes, defaults to None.
        parent_node : treelib.node, optional
            A node within a tree that has is the parent of a component, defaults to None."""
        if tree is None:
            tree = treelib.Tree()
            node = tree.create_node(tag=self.ref)
        else:
            node = tree.create_node(tag=self.ref, parent=parent_node.identifier)

        for component in self._sub_assembly.values():
            tree = component.hierarchy(tree=tree, parent_node=node)
        return tree

    def plot_hierarchy(self):
        """Creates a nice graph showing the hierachy.

        Note
        ----
        When using jupyter, the treelib.show() may not
        show as it has to be called to build a printable
        tree but also contains a print instead of returning
        the printable object."""
        tree = self.hierarchy()
        tree.show()

    def update_sub_assembly(self):
        """A class for updating a subassembly.

        This method alls the updating of the sub
        assembly, part count and master register
        if the ref has changed. .ref are not connected
        to the same datapoint as the key in sub assembly
        therefore it is ncessary to use this method.
        """
        self._part_count.clear()
        self.master_register = {self.ref: weakref.ref(self)}
        sub_list = []
        for sub in self._sub_assembly.values():
            sub_list.append(sub)
        self._sub_assembly = {}
        self.add_components(sub_list)

    def update_all_sub_asseblies(self):
        """Updates all sub assemblies in a
        assembly.
        """
        for sub in self._sub_assembly.values():
            if sub.assembly:
                sub.update_all_sub_asseblies()
        self.update_sub_assembly()


class HomogenisedAssembly(Assembly):
    """
    Information about how the HomogenisedAssembly works can be found in the
    `documentation <https://bom-analysis.readthedocs.io/en/latest/Structure_of_Hierarchy.html#homogenised-assembly-an-assembly-with-a-material>`_.
    """

    def __init__(self, ref: str = None, assignment: str = None):
        """Intitialisation of the assembly and then adds
        the default material to create a homogenised assembly."""
        super().__init__(ref=ref, assignment=assignment)
        self.add_default_material()
