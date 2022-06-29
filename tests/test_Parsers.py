import copy
import unittest
from pathlib import Path
import pprint
from unittest.mock import patch

import json
import pytest

from bom_analysis.base import BaseFramework, ConfigurationNotFullyPopulated
from bom_analysis.bom import Assembly
from bom_analysis.build import Framework
from bom_analysis.parsers import ConfigParser, SettingsParser, SkeletonParser
from bom_analysis.utils import Translator


with open(Path("./tests/test_settings.json"), "r") as f:
    SETTINGS = json.load(f)


Translator.define_translations(["./examples/files/translation.json"])


@pytest.mark.unittest
class TestSkeletonParser(unittest.TestCase):
    def setUp(self):
        self.sp = SkeletonParser()
        self.dp = self.sp.database(
            ["./tests/parents.json", "./tests/test_defined.json"]
        )

    def test_init(self):
        sp = SkeletonParser()
        assert sp.skeleton == {}

    def test_pretty_print(self):
        sp = SkeletonParser()
        print(sp)

    def test_component_database(self):
        self.assertCountEqual(
            [
                "component",
                "assembly",
                "blanket",
                "breeding_zone",
                "first_wall",
                "NEW",
                "breeder",
            ],
            list(self.dp.keys()),
        )

    def test_component_data(self):
        bz_dict = self.sp.component_data("bz", "breeding_zone", self.dp)
        assert bz_dict["inherits"] == ["assembly"]
        assert bz_dict["type"] == "breeding_zone"
        assert bz_dict["ref"] == "bz"

    def test_inherit(self):
        test_parents = {"parent": {"foo": "bar"}}
        test_comp = {"inherits": ["parent"]}
        self.sp.inherit(test_comp, test_parents)
        assert test_comp["foo"] == "bar"

    def test_all_params(self):
        test_comp = {"params_name": ["foo"]}
        test_params = {"foo": {"bar": "hello"}}
        self.sp.all_params(test_comp, test_params)
        assert test_comp["_params"]["data"] == {"bar": "hello"}
        assert "params_name" not in test_comp

    def test_all_params_old(self):
        test_comp = {"params": {"data": {"foo": "bar"}}}
        test_params = {}
        self.sp.all_params(test_comp, test_params)
        assert test_comp["_params"]["data"] == {"foo": "bar"}
        assert "params" not in test_comp

    def test_component_spine(self):
        self.sp.spine("bz", "breeding_zone", self.dp)
        self.assertCountEqual(
            list(self.sp.skeleton.keys()), ["_META", "bz", "bz_breeder"]
        )


@pytest.mark.integrationtest
class TestSkeletonToAssembly(unittest.TestCase):
    def setUp(self):
        self.blanket_1 = Assembly()
        self.blanket_2 = Assembly()
        self.sp = SkeletonParser()

    def test_component_dictionary(self):
        components = self.sp.database(
            ["./tests/parents.json", "./tests/test_defined.json"]
        )
        parameters = self.sp.database(["./tests/test_params.json"])
        skeleton = self.sp.component_dictionary(
            "new_blanket_design", "blanket", components, parameters
        )
        assert skeleton["_META"]["ref"] == "new_blanket_design"
        assert skeleton["_META"]["type"] == "blanket"
        assert skeleton["bz_breeder"]["_params"]["data"]["thickness"]["value"] is None

    def test_component_load(self):
        BaseFramework._configuration._parameters = None
        components = self.sp.database(
            ["./tests/parents.json", "./tests/test_defined.json"]
        )
        parameters = self.sp.database(["./tests/test_params.json"])
        skeleton = self.sp.component_dictionary(
            "new_blanket_design", "blanket", components, parameters
        )
        self.blanket_1.from_dict(skeleton)
        assert self.blanket_1.bz.bz_breeder.params.thickness is None


@pytest.mark.unittest
class TestConfigParser(unittest.TestCase):
    """tests the config parser"""

    def setUp(self):
        """initialises to share"""
        BaseFramework._configuration.define_config(
            config_path="./tests/test_config.json"
        )
        self.parser = ConfigParser({})

    def test_init(self):
        sp = ConfigParser({}, operate=False)
        assert sp.skeleton == {}
        assert sp._config == {}

    @patch("bom_analysis.parsers.BaseFramework._configuration")
    def test_update_config(self, config):
        config.to_dict.return_value = {
            "_parts": {"location": []},
            "_parameters": {"location": []},
            "top": "hello",
        }
        sp = ConfigParser({}, operate=False)
        sp.update_config()
        assert sp._config["parts"] == {"location": []}
        assert sp._config["top"] == "hello"
        assert sp._config["parameters"] == {"location": []}

    @unittest.expectedFailure
    @patch("bom_analysis.parsers.BaseFramework._configuration")
    def test_update_config_none_parts(self, config):
        config.to_dict.return_value = {"_parts": None, "_parameters": None}
        sp = ConfigParser({}, operate=False)
        sp.update_config()

    @unittest.expectedFailure
    @patch("bom_analysis.parsers.BaseFramework._configuration")
    def test_update_config_none_parameters(self, config):
        config.to_dict.return_value = {
            "_parts": {"location": "world"},
            "_parameters": None,
        }
        sp = ConfigParser({}, operate=False)
        sp.update_config()

    @unittest.expectedFailure
    @patch("bom_analysis.parsers.BaseFramework._configuration")
    def test_update_config_empty_parameters(self, config):
        config.to_dict.return_value = {
            "_parts": {"location": "world"},
            "_parameters": {},
        }
        sp = ConfigParser({}, operate=False)
        sp.update_config()

    @unittest.expectedFailure
    @patch("bom_analysis.parsers.BaseFramework._configuration")
    def test_update_config_empty_parts(self, config):
        config.to_dict.return_value = {"_parts": {}, "_parameters": {}}
        sp = ConfigParser({}, operate=False)
        sp.update_config()

    def test_children(self):
        """tests the child recursion works"""
        self.parser.skeleton = {}
        all_comp = {
            "foo": {"children": {"bar_ref": {"type": "bar"}}},
            "bar": {"children": {"hello_ref": {"type": "hello"}}},
            "hello": {"data": "the world"},
            "ununsed": {"data": "this should be unused"},
        }
        ref = "my_foo"
        my_foo_is = "foo"
        self.parser.children(self.parser.skeleton, all_comp, ref, {"type": my_foo_is})
        ans = {
            "my_foo": {
                "ref": "my_foo",
                "children": {"bar_ref": {"type": "bar"}},
                "type": "foo",
            },
            "bar_ref": {
                "ref": "bar_ref",
                "children": {"hello_ref": {"type": "hello"}},
                "type": "bar",
            },
            "hello_ref": {"ref": "hello_ref", "data": "the world", "type": "hello"},
        }
        self.assertDictEqual(self.parser.skeleton, ans)

    def test_spine(self):
        """tests the build of a skeleton"""
        assert type(self.parser.skeleton) == dict
        ans = ["_META", "blanket", "bz", "bz_breeder", "fw"]
        self.assertListEqual(list(self.parser.skeleton.keys()), ans)

    def test_config_build(self):
        """tests the default build from the config"""
        skeleton = self.parser.skeleton
        dict_1 = (
            {"class_str": ["bom_analysis.base.StorageClass"], "inherits": ["network"]},
        )
        list_1 = ["envelope_volume", "mass", "thickness", "volume"]
        self.assertCountEqual(list(skeleton["fw"]["_params"]["data"].keys()), list_1)

    def test_duplicates(self):
        """tests for duplications in classes"""
        for name, val in self.parser.skeleton.items():
            if name != "_META":
                assert len(set(val["class_str"])) == len(val["class_str"])

    def test_config_properties_not_overwritten(self):
        self.parser._configuration.parameters = None
        with self.assertRaises(ConfigurationNotFullyPopulated):
            should_fail = self.parser._configuration.parameters


@pytest.mark.unittest
class TestSettingsParser(unittest.TestCase):
    def setUp(self):
        """initialises to share"""
        BaseFramework._configuration.define_config(
            config_path="./tests/test_config.json"
        )
        config = ConfigParser({})
        self.parser = SettingsParser(SETTINGS, config.skeleton)

    def test_settings_update(self):
        """tests that the settings file is being read and skeleton
        updated correctly"""
        config = ConfigParser({})
        parser = SettingsParser(SETTINGS, config.skeleton)
        assert parser.skeleton["bz"]["children"]["bz_breeder"]["type"] == "beer_box"

    def test_update_settings(self):
        parser = SettingsParser({}, {}, operate=False)
        parser._settings = {"a": "b", "c": "d"}
        parser.update_settings({"c": "e"})
        assert parser._settings["c"] == "e"

    @unittest.expectedFailure
    def test_settings_input(self):
        settings = {
            "part_changes": {
                "bz": {"bz_breeder": {"type": "beer_box"}},
                "fw": {"bz_breeder": {"type": "breeder"}},
            }
        }
        skel = copy.deepcopy(self.parser.skeleton)
        test = Framework.reader(settings, skel)

    def test_part_changes(self):
        settings = {
            "parts": {"location": ["./tests/test_changes.json"]},
            "part_changes": {
                "bz": {
                    "children": {
                        "bz_shield": {"type": "component"},
                        "bz_breeder": {"type": "beer_box"},
                    }
                }
            },
        }
        skel = copy.deepcopy(self.parser.skeleton)
        parser = SettingsParser(settings, skel)
        assert "bz_shield" in skel
        assert skel["bz_breeder"]["description"] == "beer box"

    def test_settings_spine(self):
        """tests the new spine after settings have changed"""
        assert type(self.parser.skeleton) == dict
        ans = ["blanket", "bz", "bz_breeder", "bz_structure", "fw", "channel"]
        self.assertCountEqual(list(self.parser.skeleton.keys()), ans)

    def test_defaults(self):
        """tests the defaults are being assigned correctly"""
        assert (
            self.parser.skeleton["bz"]["_params"]["data"]["b2m_ratio"]["value"] == 0.2
        )

    def test_duplicates(self):
        """tests for duplications in classes"""
        for name, val in self.parser.skeleton.items():
            assert len(set(val["class_str"])) == len(
                val["class_str"]
            ), f"{name} has {val['class_str']}"

    def test_materials(self):
        """tests the material libraries can be found correctly"""
        material = {"name": "tungsten"}
        material = self.parser.select_library(material)
        material2 = {"name": "He"}
        material2 = self.parser.select_library(material2)
        assert material["class_str"] == ["bom_analysis.materials.DFLibraryWrap"]
        assert material2["class_str"] == ["bom_analysis.materials.CoolPropsWrap"]

    @unittest.expectedFailure
    def test_unknown_material(self):
        """tests the material libraries can be found correctly"""
        material = {"name": "unobtainium"}
        self.parser.select_library(material)

    def test_module_import(self):
        """tests the module requirements import"""
        assert self.parser.skeleton["bz"]["foo"] == "bar"
        assert "network" in self.parser.skeleton["blanket"]
        assert "node_count" in self.parser.skeleton["bz"]["_params"]["data"]

    def test_pprint(self):
        print("\n\n==========default==========\n\n")
        print(pprint.pformat(self.parser.skeleton, indent=4, width=1))

    def test_no_multiples(self):
        print(self.parser._config)
        assert len(self.parser.skeleton["bz"]["network"]["class_str"]) == 1

    def test_to_type_skeleton(self):
        skeleton = {
            "bz": {"type": "blanket", "mass": 100, "ref": "bz"},
            "mf": {"type": "manifold", "mass": 200, "ref": "mf"},
        }
        type_skeleton = self.parser.to_type_skeleton(skeleton)
        self.assertCountEqual(["manifold", "blanket"], list(type_skeleton.keys()))
        assert "ref" not in type_skeleton["blanket"]

    def test_config_properties_not_overwritten(self):
        self.parser._configuration.parameters = None
        with self.assertRaises(ConfigurationNotFullyPopulated):
            should_fail = self.parser._configuration.parameters


@pytest.mark.unittest
class TestFunctionality(unittest.TestCase):
    def setUp(self):
        """initialises to share"""
        BaseFramework._configuration.define_config(
            config_path="./tests/test_config.json"
        )
        config = ConfigParser({})
        self.parser = SettingsParser(SETTINGS, config.skeleton)

    def test_change_without_all_settings(self):
        """changes the part without all settings been suplied
        by loading from a previous skeleton"""
        new_components = {
            "shield_plate": {"shape": "square", "params_name": ["box_structure"]}
        }

        new_parameters = {
            "box_structure": {
                "NEWparam": {
                    "descr": None,
                    "name": "NEWparam",
                    "source": "Input",
                    "unit": "N/A",
                    "value": None,
                    "var": "NEW",
                }
            }
        }
        settings = copy.deepcopy(SETTINGS)
        settings["part_changes"] = {
            "blanket": {"children": {"new_breeding_zone": {"type": "shield_plate"}}}
        }
        parser = SettingsParser(settings, self.parser.skeleton, operate=False)
        parser.vertebrae.update(new_components)
        parser.parameters.update(new_parameters)
        parser.surgery()
        ans = {
            "shape": "square",
            "ref": "new_breeding_zone",
            "type": "shield_plate",
            "_params": {
                "class_str": ["bom_analysis.parameters.PintFrame"],
                "data": {
                    "NEWparam": {
                        "descr": None,
                        "name": "NEWparam",
                        "source": "Input",
                        "unit": "N/A",
                        "value": None,
                        "var": "NEW",
                    }
                },
            },
        }
        self.assertDictEqual(parser.skeleton["new_breeding_zone"], ans)


if __name__ == "__main__":
    unittest.main()
