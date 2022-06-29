from pathlib import Path
import unittest
from unittest.mock import MagicMock

import json
import numpy as np
import pytest

from bom_analysis import ureg, Q_
from bom_analysis.base import BaseConfig as Config
from bom_analysis.bom import Assembly, Component, HomogenisedAssembly
from bom_analysis.build import Framework


config_path = "./tests/test_config.json"
Config.define_config(config_path="./tests/test_config.json")

with open(Path("./tests/test_settings.json"), "r") as f:
    SETTINGS = json.load(f)


@pytest.mark.unittest
class TestBillOfMaterials(unittest.TestCase):
    def test_check_same_ref_and_id(self):
        """tests whether flatten works"""
        assembly = Assembly()
        comp1 = MagicMock()
        comp2 = comp1
        comp1.ref = "test"
        assembly.check_duplicate(comp1, comp2)

    @unittest.expectedFailure
    def test_check_same_ref_only(self):
        """tests whether flatten works"""
        assembly = Assembly()
        comp1 = MagicMock()
        comp2 = MagicMock()
        comp1.ref = "test"
        comp2.ref = "test"
        assembly.check_duplicate(comp1, comp2)

    def test_flatten(self):
        """tests whether flatten works"""
        assembly = Assembly()
        assembly.ref = "test"
        flat = assembly.flatten()
        assert flat["test"] == assembly

    def test_flatten_with_check(self):
        """tests whether flatten works"""
        assembly = Assembly()
        assembly.ref = "test"
        flat = assembly.flatten(dict(test=assembly))
        assert flat["test"] == assembly


@pytest.mark.unittest
class TestBillOfMaterialsHomogenisedAssembly(unittest.TestCase):
    def test_check_same_ref_and_id(self):
        """tests whether flatten works"""
        assembly = HomogenisedAssembly()
        comp1 = MagicMock()
        comp2 = comp1
        comp1.ref = "test"
        assembly.check_duplicate(comp1, comp2)

    @unittest.expectedFailure
    def test_check_same_ref_only(self):
        """tests whether flatten works"""
        assembly = HomogenisedAssembly()
        comp1 = MagicMock()
        comp2 = MagicMock()
        comp1.ref = "test"
        comp2.ref = "test"
        assembly.check_duplicate(comp1, comp2)

    def test_flatten(self):
        """tests whether flatten works"""
        assembly = HomogenisedAssembly()
        assembly.ref = "test"
        flat = assembly.flatten()
        assert flat["test"] == assembly

    def test_flatten_with_check(self):
        """tests whether flatten works"""
        assembly = HomogenisedAssembly()
        assembly.ref = "test"
        flat = assembly.flatten(dict(test=assembly))
        assert flat["test"] == assembly


@pytest.mark.regressiontest
class TestCorrectToDict(unittest.TestCase):
    def setUp(self):
        self.plane = Assembly(ref="A330")
        seating = Assembly(ref="seating")
        s34d = Component(ref="34d")
        s34e = Component(ref="34e")
        self.plane.add_component(seating)
        seating.add_components([s34e, s34d])

    def test_to_dict(self):
        skeleton = self.plane.to_dict()
        self.assertDictEqual(
            skeleton["A330"]["children"], {"seating": {"type": "seating"}}
        )

    def test_to_dict_with_type(self):
        self.plane.seating.type = "economy"
        skeleton = self.plane.to_dict()
        self.assertDictEqual(
            skeleton["A330"]["children"], {"seating": {"type": "economy"}}
        )

    def test_sub_assembly_to_child(self):
        with_type = {"type": "bar"}
        without_type = {"hello": "world"}
        child_with_type = self.plane.sub_assembly_to_child("foo", with_type)
        child_without_type = self.plane.sub_assembly_to_child("foo", without_type)
        assert child_with_type == {"foo": {"type": "bar"}}
        assert child_without_type == {"foo": {"type": "foo"}}

    def test_load_manual_defined(self):
        skeleton_1 = self.plane.to_dict()
        plane_2 = Assembly(ref="A330")
        plane_2.from_dict(skeleton_1)
        skeleton_2 = plane_2.to_dict()
        self.assertDictEqual(skeleton_1, skeleton_2)


@pytest.mark.regressiontest
class TestCorrectToDictHomogenisedAssembly(unittest.TestCase):
    def setUp(self):
        self.plane = HomogenisedAssembly(ref="A330")
        seating = HomogenisedAssembly(ref="seating")
        s34d = Component(ref="34d")
        s34e = Component(ref="34e")
        self.plane.add_component(seating)
        seating.add_components([s34e, s34d])

    def test_to_dict(self):
        skeleton = self.plane.to_dict()
        self.assertDictEqual(
            skeleton["A330"]["children"], {"seating": {"type": "seating"}}
        )

    def test_to_dict_with_type(self):
        self.plane.seating.type = "economy"
        skeleton = self.plane.to_dict()
        self.assertDictEqual(
            skeleton["A330"]["children"], {"seating": {"type": "economy"}}
        )

    def test_sub_assembly_to_child(self):
        with_type = {"type": "bar"}
        without_type = {"hello": "world"}
        child_with_type = self.plane.sub_assembly_to_child("foo", with_type)
        child_without_type = self.plane.sub_assembly_to_child("foo", without_type)
        assert child_with_type == {"foo": {"type": "bar"}}
        assert child_without_type == {"foo": {"type": "foo"}}

    def test_load_manual_defined(self):
        skeleton_1 = self.plane.to_dict()
        plane_2 = Assembly(ref="A330")
        plane_2.from_dict(skeleton_1)
        skeleton_2 = plane_2.to_dict()
        self.assertDictEqual(skeleton_1, skeleton_2)


@pytest.mark.integrationtest
class TestBOMIntegration(unittest.TestCase):
    def setUp(self):
        self.assy1 = Assembly(ref="foo")
        self.assy2 = Assembly(ref="hello")
        self.comp1 = Component(ref="bar")
        self.comp2 = Component(ref="bar")

    def test_ref_mutability(self):
        self.assy1.add_components([self.comp2])
        self.comp2.ref = "changed"
        self.assy1.update_all_sub_asseblies()
        assert self.assy1.changed.ref == "changed"
        assert self.assy1.count_ref("bar") == 0
        assert self.assy1.count_ref("changed") == 1
        assert "bar" not in self.assy1.master_register

    def test_ref_to_dict(self):
        assy3 = Assembly(ref="world")
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([assy3])
        assy3.add_components([self.comp2])
        output_dict = self.assy1.to_dict()
        assert "master_register" not in output_dict["foo"]
        assert "_sub_assembly" not in output_dict["foo"]
        assert "master_register" not in output_dict["hello"]
        assert "_sub_assembly" not in output_dict["hello"]
        assert "master_register" not in output_dict["world"]
        assert "_sub_assembly" not in output_dict["world"]

    def test_count(self):
        self.assy1.add_components([self.comp2, self.comp2])
        assert self.assy1.bar.ref == "bar"
        assert self.assy1.count_ref("bar") == 2
        assert self.assy1.count_ref("foo") == 0

    def test_sub_same_ref_same_id(self):
        self.assy2.add_components([self.comp2])
        self.assy1.add_components([self.comp2, self.assy2])
        assert self.assy1.bar == self.assy2.bar

    def test_sub_same_ref_same_id_level(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        assert self.assy1.bar == self.assy2.bar
        assert self.assy1.bar == self.assy1.hello.bar

    def test_add_twice(self):
        comp3 = Component(ref="world")
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])

        assert self.assy1.count_ref("hello") == 2

    def test_remove_component(self):
        comp3 = Component(ref="world")
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])
        assert "world" in self.assy1.master_register.keys()
        self.assy2.remove_component("world")
        self.assy1.update_all_sub_asseblies()
        print(self.assy1.plot_hierarchy())
        print(self.assy1.master_register)
        self.assertCountEqual(self.assy2.flatten().keys(), ["bar", "hello"])
        self.assertCountEqual(
            self.assy1.master_register.keys(), ["foo", "bar", "hello"]
        )
        self.assertCountEqual(
            self.assy2.master_register.keys(), ["foo", "bar", "hello"]
        )
        assert "world" not in self.assy2._sub_assembly.keys()

    def test_remove_component_mulitples(self):
        comp3 = Component(ref="world")
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])
        self.assy1.remove_component("hello")
        self.assy1.update_all_sub_asseblies()
        assert self.assy1.count_ref("hello") == 1
        assert "hello" in self.assy1.flatten().keys()

    def test_remove_component_not_in_assy(self):
        self.assy1.remove_component("hello")

    def test_remove_assembly(self):
        comp3 = Component(ref="world")
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.add_components([self.assy2])
        self.assy2.add_components([self.comp2, comp3])
        self.assy1.remove_component("hello")
        self.assy1.update_all_sub_asseblies()
        self.assertCountEqual(self.assy1.flatten().keys(), ["foo"])
        self.assertCountEqual(self.assy1.master_register.keys(), ["foo"])

    def test_super_low_all(self):
        assy3 = Assembly(ref="world")
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([assy3])
        assy3.add_components([self.comp2])
        self.assertCountEqual(
            self.assy1.master_register.keys(), ["world", "foo", "bar", "hello"]
        )

    @unittest.expectedFailure
    def test_sub_same_ref_dif_id_fail(self):
        self.assy2.add_components([self.comp1])
        self.assy1.add_components([self.comp2, self.assy2])

    @unittest.expectedFailure
    def test_sub_same_ref_dif_id_level_fail(self):
        self.assy1.add_components([self.assy2, self.comp1])
        self.assy2.add_components([self.comp2])

    @unittest.expectedFailure
    def test_super_low_fail(self):
        assy3 = Assembly(ref="world")
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([assy3])
        assy3.add_components([self.comp1])

    def test_add_default(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        self.assy1.add_defaults(dict(bar={"mass": Q_(100, "kg")}))
        assert self.assy1.bar.params.mass.to("kg").m == 100

    def test_add_default_multi(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        self.assy1.add_defaults(dict(bar={"mass": 100 * ureg("kg")}))
        assert self.assy1.bar.params.mass.to("kg").m == 100

    def test_material_assignment(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        self.comp2.material.mat = "tungsten"
        self.comp2.material.reftemp = Q_(500, "degC")
        self.comp2.material.pressure = Q_(80, "bar")
        self.assy1.assign_all_materials()
        assert self.comp2.material.data_wrapper("thermal_conductivity").m == 170.0
        assert self.comp2.material.reftemp.m == 500
        assert self.comp2.material.pressure.m == 80

    def test_to_dict(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        data = self.assy1.to_dict()

        new_assy = Assembly(ref="hello")
        new_assy.from_dict(data)

        for comp in new_assy.flatten().values():
            assert hasattr(comp, "_ref")

    def test_to_copy_duplicate_in_bom(self):
        self.assy1.add_components([self.comp2, self.assy2])
        self.assy2.add_components([self.comp2])
        self.assy1.plot_hierarchy()
        new_assy = self.assy1.copy_part()

        for comp in new_assy.flatten().values():
            assert hasattr(comp, "_ref")

        self.assertCountEqual(
            list(new_assy.master_register.keys()), ["foo", "hello", "bar"]
        )

    def test_to_copy_duplicate_deeply_nested(self):
        a = Assembly(ref="a")
        b = Assembly(ref="b")
        c = Assembly(ref="c")
        d = Component(ref="d")

        a.add_component(b)
        b.add_component(c)
        c.add_component(d)

        new_a = a.copy_part()

        assert id(a.b.c.d) != id(new_a.b.c.d)

    def test_assignment(self):
        new_component = Component(ref="hello", assignment="world")
        self.assertCountEqual(new_component._assignment, ["world"])

        new_component = Component(ref="hello", assignment=["foo", "bar"])
        self.assertCountEqual(new_component._assignment, ["foo", "bar"])

        new_component = Component(ref="hello", assignment=np.array(["foo", "bar"]))
        self.assertCountEqual(new_component._assignment, ["foo", "bar"])


@pytest.mark.unittest
class TestFramework(unittest.TestCase):
    """test for the framework"""

    def setUp(self):
        """sets up test"""

        pass

    def test_component(self):
        """tests that a component can be correctly populated"""

        skel = {
            "widget": {"material": {"class_str": ["pandas.DataFrame"]}},
            "description": "a widget",
        }
        widget = Component()
        widget.from_dict(skel, ref="widget")
        assert widget.material.class_str == ["pandas.DataFrame"]
        assert widget.material.to_dict() == {}

    def test_assemby(self):
        """tests an assembly"""
        skel = {
            "widget": {
                "class_str": ["bom_analysis.bom.Component"],
                "material": {"class_str": ["pandas.DataFrame"]},
                "description": "a widget",
            },
            "big_widget": {
                "description": "an assembly widget",
                "children": {"widget": {}},
            },
        }
        big_widget = Assembly()
        big_widget.from_dict(skel, ref="big_widget")

        assert big_widget.widget.material.class_str[0] == "pandas.DataFrame"
        assert big_widget.widget.material.to_dict() == {}
        assert big_widget.description == "an assembly widget"

    def test_change_network(self):
        """tests that data can be written to storage classes"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        self.populated.bz.network.create_df(5, "a", "b", "c", "d")
        self.populated.bz.network.data.at[3, "b"] = "hello"
        # print(self.populated.params)
        self.populated.params.mass = 100000 * ureg("lb")
        assert self.populated.bz.network.data["b"][3] == "hello"
        assert self.populated.params.mass == 100000 * ureg("lb")

    @unittest.expectedFailure
    def test_params_fail(self):
        """tests that you cannot supply a non pint value to params"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        self.populated.params.mass = 100000 * ureg("lb")
        self.populated.params.volume = 100000

    def test_settings_build(self):
        """tests the top level of the assembly"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        check = self.populated.bz.bz_breeder.channel.params.get_param(
            "mass", key="name"
        )
        assert check == "mass of the component"

    def test_dicts_added(self):
        """tests that non specified storage like dicts are added"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        assert self.populated.bz.description == "component within assembly"

    def test_skeleton_dump(self):
        """checks the format of the skeleton is dumped"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        self.populated.bz.network.create_df(5, "a", "b", "c", "d")
        self.populated.bz.network.data.at[3, "b"] = "hello"
        self.populated.params.mass = 100000 * ureg("lb")
        dump = self.populated.to_dict()
        output = json.dumps(dump)
        ans = ["fw", "bz", "bz_breeder", "channel", "bz_structure", "blanket"]
        self.assertCountEqual(list(dump.keys()), ans)

    def test_read_write(self):
        """checks that a skeleton is input and output with no changes"""
        framework = Framework(config_path=config_path)
        self.populated = Framework.reader(framework.skeleton, settings=SETTINGS)
        self.populated.bz.network.create_df(5, "a", "b", "c", "d")
        self.populated.bz.network.data.at["b", 3] = "hello"
        self.populated.params.mass = 100000 * ureg("lb")

        dump1 = self.populated.to_dict()
        new_assy = Assembly()
        new_assy.from_dict(dump1, ref="blanket")
        dump2 = new_assy.to_dict()
        # for name in dump1:
        #     print(f"========={name}=========")
        #     pprint.pprint(framework.skeleton[name])
        #     pprint.pprint(dump1[name])

        self.assertDictEqual(dump1, dump2)
        assert new_assy.bz.network.data.at["b", 3] == "hello"
        self.assertAlmostEqual(new_assy.params.mass, 100000 * ureg("lb"))

    def test_comp_from_str(self):
        """test the component from string is working correctly"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        comp1 = assembly.component_from_string("blanket.bz.bz_breeder.bz_structure")
        comp2 = assembly.component_from_string("fw")
        assert comp1.type == "grid"
        assert comp2.geometry["section"] == "rectangular"

    def test_flatten(self):
        """tests whether flatten works"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        flatten = assembly.flatten()
        assert flatten["blanket"] == assembly
        assert flatten["fw"].material.name == "tungsten"

    def test_module_import(self):
        """tests the module requirements import"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        assert assembly.bz.foo == "bar"

    def test_assembly_check(self):
        """tests that assembly property working"""
        framework = Framework(config_path=config_path)
        blanket = Framework.reader(framework.skeleton, settings=SETTINGS)
        assert blanket.assembly
        assert not blanket.bz.bz_breeder.bz_structure.assembly

    def test_sub_params(self):
        """tests the module requirements import"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        parameters = assembly.lookup_params("volume")
        materials = assembly.lookup("material")
        volume = sum(
            [
                param["volume"]
                for param in parameters.values()
                if param["volume"] is not None
            ]
        )
        assert volume.magnitude == 300
        assert materials["channel"]["material"].name == "He"
        # print(assembly.sub_params_list(["volume"]))

    def test_copy_part(self):
        """tests that a part can be correctly copied"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        new_fw = assembly.fw.copy_part()
        new_assembly = assembly.copy_part()

        assert id(assembly) != id(new_assembly)
        assert id(new_fw) != id(assembly.fw)

    def test_hierarchy(self):
        """tests the hierarchy can be populated properly"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        tree = assembly.plot_hierarchy()

    def test_repr(self):
        """tests the hierarchy can be populated properly"""
        framework = Framework(config_path=config_path)
        assembly = Framework.reader(framework.skeleton, settings=SETTINGS)
        print(assembly)


if __name__ == "__main__":
    unittest.main()
