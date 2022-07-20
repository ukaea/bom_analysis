import unittest

import json
import numpy as np
import pandas as pd
import pytest

from bom_analysis import Q_
import bom_analysis.base as bs
from bom_analysis.base import BaseConfig as Config
from bom_analysis.bom import Assembly, Component
from bom_analysis.utils import class_from_string


class TestBaseClass(unittest.TestCase):
    def setUp(self):
        self.base = bs.BaseClass()

        self.base.data = {
            "a": np.array([np.float64(4.0), {"hello": "world"}], dtype=object)
        }

        base2 = bs.BaseClass()

        base2.foo = {"b": np.int64(42)}

        self.base.child = {"sub": base2}

        self.base.df = pd.DataFrame({"test": [1, 2], "data": [3, 4]})

    def test_classfromstring(self):
        """test the class from string"""
        str1 = "bom_analysis.parameters.PintFrame"
        cls1 = class_from_string(str1)()
        str2 = "numpy.array"
        cls2 = class_from_string(str2)([1, 2])
        cls2 += 1
        assert cls1._data == {}
        assert cls2[0] == 2
        assert cls2[1] == 3

    def test_ToJson(self):
        """tests whether to_dict works for different cases"""
        dump = self.base.to_dict()
        output = json.dumps(dump)
        assert type(dump["data"]["a"]) == list
        assert type(dump["df"]) == dict
        assert dump["child"]["sub"]["foo"]["b"] == 42

    def test_FromJson(self):
        """tests whether to_dict works for different cases"""
        dump = self.base.to_dict()

        new_base = bs.BaseClass()
        new_base.from_dict(dump)

        assert type(new_base.data) == dict
        assert new_base.child["sub"]["foo"]["b"] == 42


class TestStorageClass(unittest.TestCase):
    def setUp(self):
        self.dfclass = bs.DFClass()
        component = Component()
        component.ref = "com1"
        component.df = bs.DFClass()
        component.df.create_df(2, "a", "b")
        component.df.add_to_col(0, {"a": 1})

        component2 = Component()
        component2.ref = "com2"
        component2.df = bs.DFClass()
        component2.df.create_df(2, "a", "b")
        component2.df.add_to_col(1, {"a": 1, "b": 2})

        component3 = Component()
        component3.ref = "com3"
        component3.df = bs.DFClass()
        component3.df.create_df(1, "a", "b")

        sa = Assembly()
        sa.ref = "sub_assembly"
        self.assembly = Assembly()
        self.assembly.ref = "assem"
        sa.add_component(component)
        self.assembly.add_component(sa)
        self.assembly.add_component(component2)
        self.assembly.add_component(component3)
        self.assembly.df = bs.DFClass()

    def test_df(self):
        """tests creating the dataframe"""
        self.dfclass.create_df(5, "a", "b", "c")
        self.dfclass.data.at["b", 3] = "hello"
        assert self.dfclass.data[3]["b"] == "hello"
        self.assertCountEqual(
            self.dfclass.vars,
            (
                "a",
                "b",
                "c",
            ),
        )

    def test_ToJson(self):
        self.dfclass.create_df(5, "a", "b", "c")
        self.dfclass.data.at["b", 3] = "hello"
        self.dfclass.data.at["c", 4] = np.array([1, 2])
        self.dfclass.fluid = "water"
        dump = self.dfclass.to_dict()
        output = json.dumps(dump)
        assert dump["data"]["data"][1][3] == "hello"

    def test_FromJson(self):
        """tests a load from json"""
        self.dfclass.create_df(5, "a", "b", "c")
        self.dfclass.data.at["b", 3] = "hello"
        self.dfclass.data.at["c", 4] = np.array([1, 2])
        self.dfclass.fluid = "water"
        dump = self.dfclass.to_dict()
        # print(dump)
        new_class = bs.DFClass()
        new_class.from_dict(dump)
        assert isinstance(new_class.data.at["c", 4], np.ndarray)
        assert new_class.fluid == "water"
        assert new_class.data.at["b", 3] == "hello"

    def test_AddData(self):
        """tests the addition of data to the dataframe"""
        self.dfclass.create_df(5, "a", "b", "c")
        self.dfclass.add_to_col(0, {"a": 1})
        self.dfclass.add_to_col(1, {"a": 1, "b": 2, "c": 3})
        assert self.dfclass.data.at["b", 0] == None
        assert self.dfclass.data.at["a", 0] == 1
        assert self.dfclass.data.at["b", 1] == 2

    def test_compile_all_df(self):
        """checks lower level compelations can be created
        used to create a top level df"""
        self.assembly.df.compile_all_df(self.assembly, "df")
        self.assertCountEqual(self.assembly.df.vars, ["a", "b"])
        assert self.assembly.df.col_count == 5
        assert self.assembly.df.data.at["a", 0] == 1
        assert self.assembly.df.data.at["a", 1] == None
        assert self.assembly.df.data.at["b", 3] == 2

    def test_assign(self):
        df1 = pd.DataFrame(index=["foo", "bar", "baz", "foobar"], data=[1, 2, 3, 5])
        df2 = pd.DataFrame(index=["foo", "bar", "hello", "world"], data=[5, 6, 7, 8])

        wrapped = bs.DFClass()
        wrapped.assign(df1)
        wrapped.assign(df2)
        self.assertCountEqual(
            list(wrapped.vars), ["foo", "bar", "baz", "foobar", "hello", "world"]
        )


class TestConfig(unittest.TestCase):
    def test_DictInput(self):
        """tests config can be loaded from dict"""
        config = {"a": 1, "b": "foo", "c": "bar"}
        Config.define_config(config_dict=config)
        assert Config.a == 1

    def test_PathInput(self):
        """tests the config can be loaded from a path"""
        Config.define_config(config_path="./tests/test_config.json")
        assert Config.top["ref"] == "blanket"

    def test_BothInput(self):
        """tests a path and a dict config can be merged"""
        config = {"parts": {"location": ["foobar"]}, "b": "foo", "c": "bar"}
        Config.define_config(config_path="./tests/test_config.json", config_dict=config)
        self.assertCountEqual(
            Config.parts["location"],
            ["./tests/parents.json", "./tests/test_defined.json", "foobar"],
        )

    def test_to_dict(self):
        """tests config can export to dict"""
        config = {"a": 1, "b": "foo", "c": "bar"}
        Config.define_config(config_dict=config)
        con = Config.to_dict()
        assert con["b"] == "foo"

    def test_to_dict_without_login(self):
        """tests whether to_dict works for different cases"""
        config = {"a": 1, "b": "foo", "c": "bar"}
        Config.define_config(config_dict=config)
        Config._login_details = {
            "username": "secret",
            "password": "secret",
            "domain": "secret",
        }
        dump = Config.to_dict()
        assert "_login_details" not in dump

    def test_assignment_to_property(self):
        Config.restrict_param = "hello"
        assert Config.restrict_param == "hello"

    def test_setattr(self):
        setattr(Config, "restrict_param", "hello")
        assert Config.restrict_param == "hello"

    def test_materials_can_not_have_str(self):
        with self.assertRaises(TypeError):
            Config.materials = "foobar"

    @unittest.expectedFailure
    def test_assignment_to_parameters(self):
        """check to make sure property has not been overwritten"""
        Config.parameters = "hello"
        assert Config.parameters == "hello"
        Config.parameters = None
        assert Config.parameters is None

    def test_assignment_to_property_with_data_lib(self):
        print("in test", Config.data_dir)
        test = Config.data_dir
        import os

        assert test == os.getcwd()

    def test_assignment_to_property_with_data_dir_try(self):
        from bom_analysis.base import ConfigurationNotFullyPopulated

        try:
            test = Config.data_dir
        except ConfigurationNotFullyPopulated:
            pass

    def test_not_implemented_meta(self):
        from bom_analysis.base import MetaConfig

        class MyNewConfig(metaclass=MetaConfig):
            pass

        config = MyNewConfig
        with self.assertRaises(NotImplementedError):
            config.to_dict()

        with self.assertRaises(NotImplementedError):
            config.temp_dir = "./temp/"


@pytest.mark.integrationtest
class TestOldFormatLoad(unittest.TestCase):
    def setUp(self):
        self.data_dictionary_old = {
            "phone": {
                "_assignment": [],
                "children": {
                    "case": {"type": "phone_case"},
                    "batery": {"type": "phone_batery"},
                },
                "class_str": ["bom_analysis.bom.Assembly"],
                "description": "a smart phone",
                "inherited": ["assembly"],
                "params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "the phones mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.03,
                            "var": "mass",
                        }
                    },
                },
                "ref": "phone",
                "type": "smart_phone",
            },
            "batery": {
                "_assignment": [],
                "class_str": ["bom_analysis.bom.Component"],
                "description": "a fusion powerplant",
                "inherited": ["assembly"],
                "params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "teh battery mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.02,
                            "var": "mass",
                        }
                    },
                },
                "ref": "batery",
                "type": "phone_batery",
                "material": {
                    "_mat": "lithium",
                    "class_str": [
                        "bom_analysis.materials.DFLibraryWrap",
                        "bom_analysis.materials.Solid",
                    ],
                    "enrichment": None,
                    "inherited": ["solid"],
                    "path": "./examples/files/example_material_properties.json",
                    "name": "tungsten",
                    "nuclear_material": None,
                    "pressure": "200000000.0 gram / meter / second ** 2",
                    "reftemp": "675.7551884880228 kelvin",
                    "translate_to": "example_properties",
                },
            },
            "case": {
                "_assignment": [],
                "class_str": ["bom_analysis.bom.Component"],
                "description": "a phone case",
                "inherited": ["assembly"],
                "params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "the cases mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.01,
                            "var": "mass",
                        }
                    },
                },
                "ref": "case",
                "type": "phone_case",
                "material": {
                    "class_str": ["bom_analysis.materials.Composition"],
                    "enrichment": None,
                    "inherited": ["homogenised"],
                    "name": "blanket_mat",
                    "nuclear_material": {
                        "case": {
                            "decimal_places": 8,
                            "density": 7.666825711211839,
                            "density_unit": "g/cm3",
                            "isotopes": {"Al27": 1.00},
                            "packing_fraction": 1.0,
                            "percent_type": "ao",
                        },
                        "name": "case_mat",
                    },
                    "reftemp": "673.15 kelvin",
                },
            },
        }

        self.data_dictionary_new = {
            "phone": {
                "_assignment": [],
                "children": {
                    "case": {"type": "phone_case"},
                    "batery": {"type": "phone_batery"},
                },
                "class_str": ["bom_analysis.bom.Assembly"],
                "description": "a smart phone",
                "inherited": ["assembly"],
                "_params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "the phones mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.03,
                            "var": "mass",
                        }
                    },
                },
                "_ref": "phone",
                "type": "smart_phone",
            },
            "batery": {
                "_assignment": [],
                "class_str": ["bom_analysis.bom.Component"],
                "description": "a phone battery",
                "inherited": ["assembly"],
                "_params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "the battery mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.02,
                            "var": "mass",
                        }
                    },
                },
                "_ref": "batery",
                "type": "phone_batery",
                "_material": {
                    "_mat": "lithium",
                    "class_str": [
                        "bom_analysis.materials.DFLibraryWrap",
                        "bom_analysis.materials.Solid",
                    ],
                    "enrichment": None,
                    "inherited": ["solid"],
                    "path": "./examples/files/example_material_properties.json",
                    "name": "lithium",
                    "nuclear_material": None,
                    "pressure": "200000000.0 gram / meter / second ** 2",
                    "reftemp": "675.7551884880228 kelvin",
                    "translate_to": "example_properties",
                },
            },
            "case": {
                "_assignment": [],
                "class_str": ["bom_analysis.bom.Component"],
                "description": "a phone case",
                "inherited": ["assembly"],
                "_params": {
                    "class_str": ["bom_analysis.parameters.PintFrame"],
                    "data": {
                        "mass": {
                            "descr": None,
                            "name": "the cases mass",
                            "source": "Input",
                            "unit": "kg",
                            "value": 0.01,
                            "var": "mass",
                        }
                    },
                },
                "_ref": "case",
                "type": "phone_case",
                "_material": {
                    "class_str": ["bom_analysis.materials.Composition"],
                    "enrichment": None,
                    "inherited": ["homogenised"],
                    "name": "case_mat",
                    "nuclear_material": {
                        "case": {
                            "decimal_places": 8,
                            "density": 7.666825711211839,
                            "density_unit": "g/cm3",
                            "isotopes": {"Al27": 1.00},
                            "packing_fraction": 1.0,
                            "percent_type": "ao",
                        },
                        "name": "case_mat",
                    },
                    "reftemp": "673.15 kelvin",
                },
            },
        }

    def test_load_old_correctly(self):
        phone = Assembly()
        phone.from_dict(self.data_dictionary_old, ref="phone")
        phone.plot_hierarchy()
        print(phone.params)

    def test_load_new_correctly(self):
        phone = Assembly()
        phone.from_dict(self.data_dictionary_new, ref="phone")
        phone.plot_hierarchy()
        print(phone.params)


class TestBaseDfClass(unittest.TestCase):
    def test_print_correctly(self):
        df_wrap = bs.DFClass()
        df_wrap.create_df(4, "foo", "bar")
        print(df_wrap)

    def test_print_empty(self):
        df_wrap = bs.DFClass()
        print(df_wrap)

    def test_print_correctly_with_pint(self):
        df_wrap = bs.DFClass()
        df_wrap.create_df(4, "foo", "bar")
        df_wrap.data.at["foo", 1] = Q_(1000, "meter*meter*kilogram*litre")
        print(df_wrap)


if __name__ == "__main__":

    unittest.main()
