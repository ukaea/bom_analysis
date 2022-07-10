import unittest
from unittest.mock import MagicMock, patch

import pytest

from bom_analysis import ureg, Q_
from bom_analysis.base import BaseFramework
from bom_analysis.materials import (
    MaterialData,
    NoMaterialDataException,
    DFLibraryWrap,
    CoolPropsWrap,
)
from bom_analysis.utils import MaterialSelector, Translator, class_factory


@pytest.mark.unittest
class TestMaterialSelector(unittest.TestCase):
    def test_add_database(self):
        ms = MaterialSelector()
        ms.add_database(dict, {})
        ms.add_database(list, {"hello": "world"})
        assert ms.priority_order[0] == dict(material=dict, data={})
        assert ms.priority_order[1] == dict(material=list, data={"hello": "world"})

    def test_to_dict(self):
        ms = MaterialSelector()
        ms.add_database(dict, {})
        ms.add_database(list, {"hello": "world"})
        output = ms.to_dict()
        assert output[0]["class_str"] == ["builtins.dict"]
        assert output[1]["data"] == {"hello": "world"}

    def test_old_style_from_dict(self):
        old = {
            "order": {"0": "a_dictionary", "1": "a_list"},
            "a_dictionary": {"class_str": ["builtins.dict"]},
            "a_list": {"class_str": ["builtins.list"], "hello": "world"},
        }
        ms = MaterialSelector()
        ms.old_style_from_dict(old)
        test_dict = ms.priority_order[0]["material"]()
        test_dict["foo"] = "bar"
        test_list = ms.priority_order[1]["material"]()
        test_list.append("foo")
        assert test_dict == dict(foo="bar")
        assert test_list == ["foo"]
        assert ms.priority_order[1]["data"] == {
            "class_str": ["builtins.list"],
            "hello": "world",
        }

    @unittest.expectedFailure
    def test_old_style_from_dict_two_class(self):
        old = {
            "order": {"0": "a_dictionary", "1": "a_list"},
            "a_dictionary": {"class_str": ["builtins.dict", "builtins.list"]},
            "a_list": {"class_str": ["builtins.list"], "hello": "world"},
        }
        ms = MaterialSelector()
        ms.old_style_from_dict(old)

    def test_from_dict_with_old(self):
        old = {
            "order": {"0": "a_dictionary", "1": "a_list"},
            "a_dictionary": {"class_str": ["builtins.dict"]},
            "a_list": {"class_str": ["builtins.list"], "hello": "world"},
        }
        ms = MaterialSelector()
        ms.from_dict(old)
        test_dict = ms.priority_order[0]["material"]()
        test_dict["foo"] = "bar"
        test_list = ms.priority_order[1]["material"]()
        test_list.append("foo")
        assert test_dict == dict(foo="bar")
        assert test_list == ["foo"]
        assert ms.priority_order[1]["data"] == {
            "class_str": ["builtins.list"],
            "hello": "world",
        }

    def test_from_dict(self):
        new = [
            {"class_str": "builtins.dict", "data": {}},
            {"class_str": "builtins.list", "data": {"hello": "world"}},
        ]
        ms = MaterialSelector()
        ms.from_dict(new)
        test_dict = ms.priority_order[0]["material"]()
        test_dict["foo"] = "bar"
        test_list = ms.priority_order[1]["material"]()
        test_list.append("foo")
        assert test_dict == dict(foo="bar")
        assert test_list == ["foo"]
        assert ms.priority_order[1]["data"] == {
            "class_str": "builtins.list",
            "hello": "world",
        }

    def test_initialised_database(self):
        ms = MaterialSelector()
        database = dict(material=MagicMock, data={"hello": "world"})
        new_instance = ms.intialised_database(material_str="foo", database=database)
        assert new_instance.mat == "foo"
        assert new_instance.hello == "world"


@pytest.mark.integrationtest
class TestMaterialsWithSelector(unittest.TestCase):
    def test_database_selection(self):
        ms = MaterialSelector()
        ms.add_database(
            DFLibraryWrap,
            dict(path="./examples/files/example_material_properties.json"),
        )
        ms.add_database(CoolPropsWrap)
        steel_database = ms.select_database("steel")
        helium_database = ms.select_database("He")

        assert steel_database.mat == "steel"
        assert steel_database.extract_property("thermal_conductivity").m == 28.3
        assert helium_database.mat == "He"
        self.assertAlmostEqual(
            helium_database.extract_property("conductivity").m, 0.153, 3
        )
        self.assertAlmostEqual(
            helium_database.extract_property("viscosity").m, 1.960730243278851e-05, 3
        )


@pytest.mark.unittest
class TestMaterialData(unittest.TestCase):
    def setUp(self):
        self.mat = MaterialData()

    def test_init_kwargs(self):
        mat = MaterialData(temp=100)
        assert mat.temperature == 100

    def test_init(self):
        mat = MaterialData(mat="test", temperature=50, pressure=1)
        assert mat.mat == "test"
        assert mat.temperature == 50
        assert mat.pressure == 1

    def test_add_defaults(self):
        mat = MaterialData()
        mat.add_defaults(dict(mat="test", temperature=50, pressure=1))
        assert mat.mat == "test"
        assert mat.temperature == 50
        assert mat.pressure == 1

    def test_legacy_methods(self):
        self.mat.SetRefPressure(pressure=1)
        assert self.mat.pressure == 1
        self.mat.SetLibMaterial("test")
        assert self.mat.mat == "test"
        self.mat.SetRefTemp(Temp=50)
        assert self.mat.temperature == 50

    def test_check(self):
        with pytest.raises(NotImplementedError):
            self.mat.check("test")

    def test_extract_property(self):
        with pytest.raises(NotImplementedError):
            self.mat.extract_property("test")


@pytest.mark.integrationtest
class TestMaterials(unittest.TestCase):
    """test for the bom_analysis"""

    def setUp(self):
        Translator.define_translations(["./examples/files/translation.json"])
        skeleton = {
            "class_str": [
                "bom_analysis.materials.DFLibraryWrap",
                "bom_analysis.materials.Solid",
            ],
            "name": "tungsten",
            "path": "./examples/files/example_material_properties.json",
            "translate_to": "example_properties",
        }

        self.solid = class_factory("solid", skeleton["class_str"], skeleton)
        self.solid.from_dict(skeleton)

        skeleton = {
            "class_str": [
                "bom_analysis.materials.CoolPropsWrap",
                "bom_analysis.materials.Fluid",
            ],
            "name": "H2O",
            "translate_to": "CoolProps",
        }
        self.fluid = class_factory("fluid", skeleton["class_str"], skeleton)
        self.fluid.from_dict(skeleton)

    def test_solid_inheritance(self):
        """test the solid have been inherited correctly"""
        assert self.solid._mat == "tungsten"
        assert self.solid.data_wrapper("thermal_conductivity") == 170.0 * ureg("W/m*K")

    def test_fluid_inheritance(self):
        """test the fluid have been inherited correctly"""
        assert self.fluid._mat == "H2O"
        assert int(self.fluid.data_wrapper("density").m) == 998

    def test_to_json(self):
        """tests correctly writes to json format"""
        self.solid.SetRefTemp(Temp=500.0 * ureg("K"))
        fluid_dump = self.fluid.to_dict()
        solid_dump = self.solid.to_dict()

        solid2 = class_factory("solid", solid_dump["class_str"], solid_dump)
        solid2.from_dict(solid_dump)
        assert solid2.reftemp.magnitude == 500.0
        solid2_dump = solid2.to_dict()
        self.assertDictEqual(solid_dump, solid2_dump)

        assert solid2.reftemp == 500.0 * ureg("K")
        assert solid2_dump["_temperature"] == "500.0 kelvin"


@pytest.mark.integrationtest
class TestMaterialsExceptions(unittest.TestCase):
    def setUp(self):
        Translator.define_translations(["./examples/files/translation.json"])
        skeleton = {
            "class_str": [
                "bom_analysis.materials.DFLibraryWrap",
                "bom_analysis.materials.Solid",
            ],
            "name": "steel",
            "path": "./examples/files/example_material_properties.json",
        }

        self.solid = class_factory("solid", skeleton["class_str"], skeleton)
        self.solid.from_dict(skeleton)

    def test_correct_exception(self):
        """test the solid have been inherited correctly"""
        with self.assertRaises(NoMaterialDataException):
            self.solid.extract_property("no_property")

    @patch("bom_analysis.materials.BaseFramework._configuration")
    def test_scaled_search(self, config_patch):
        config_patch.materials = MaterialSelector()
        config_patch.materials.add_database(
            DFLibraryWrap, {"path": "./examples/files/example_material_properties.json"}
        )
        config_patch.materials.add_database(
            DFLibraryWrap, {"path": "./tests/test_material.json"}
        )
        ans = self.solid.data_wrapper("made_up_property")
        assert ans.m == 100  #

    @patch("bom_analysis.materials.BaseFramework._configuration")
    def test_scaled_search_old_style(self, config_patch):
        config_patch.materials = MaterialSelector()
        config_patch.materials.from_dict(
            {
                "order": {"0": "TestMaterialDatabase1", "1": "TestMaterialDatabase2"},
                "TestMaterialDatabase1": {
                    "class_str": ["bom_analysis.materials.DFLibraryWrap"],
                    "path": "./examples/files/example_material_properties.json",
                },
                "TestMaterialDatabase2": {
                    "class_str": ["bom_analysis.materials.DFLibraryWrap"],
                    "path": "./tests/test_material.json",
                },
            }
        )
        ans = self.solid.data_wrapper("made_up_property")
        assert ans.m == 100

    def test_scaled_search_new_style_no_patch(self):
        ms = MaterialSelector()
        ms.add_database(
            DFLibraryWrap, {"path": "./examples/files/example_material_properties.json"}
        )
        ms.add_database(DFLibraryWrap, {"path": "./tests/test_material.json"})
        BaseFramework._configuration.materials = ms
        ans = self.solid.data_wrapper("made_up_property")
        assert ans.m == 100


@pytest.mark.regressiontest
class TestMaterialsRegression(unittest.TestCase):
    def test_scaled_search_new_style_regression(self):
        """regression test found in juypter"""
        from bom_analysis.utils import Translator

        Translator.define_translations(["./examples/files/translation.json"])
        ms = MaterialSelector()
        ms.add_database(
            DFLibraryWrap, {"path": "./examples/files/example_material_properties.json"}
        )
        ms.add_database(CoolPropsWrap)
        from bom_analysis.base import BaseConfig as Config

        Config.materials = ms
        co2 = Config.materials.select_database("CarbonDioxide")
        self.assertAlmostEqual(
            co2.data_wrapper("thermal_conductivity").to("K*W/m").m, 0.0166
        )
        self.assertAlmostEqual(co2.data_wrapper("density").to("kg/m**3").m, 1.81611, 5)


testdata = [
    ("He", "D", Q_(0.016429320327618305, "kg/m**3")),
    ("He", "T", Q_(293, "K")),
    ("He", "P", Q_(10000.0, "Pa")),
    ("He", "C", Q_(5193.1637195563435, "J/kg")),
    ("He", "O", Q_(3115.920621402665, "J/kg")),
    ("He", "U", Q_(918103.1469226304, "J/kg")),
    ("He", "H", Q_(1526771.0528730445, "J/kg")),
    ("He", "S", Q_(32697.126252868744, "J/kg/K")),
    ("He", "A", Q_(1007.2182633409453, "m/s")),
    ("He", "G", Q_(-8053486.9392174985, "J/kg")),
    ("He", "V", Q_(1.960730243278851e-05, "Pa*s")),
    ("He", "L", Q_(0.15337937761347065, "W/m/K")),
]


@pytest.mark.integrationtest
@pytest.mark.parametrize("mat,output,ans", testdata)
def test_coolprops_units_unchanged(mat, output, ans):
    """tests co2 in coolprops"""
    material = CoolPropsWrap(
        mat=mat, temp=Q_(293, "K").to("degC"), pressure=Q_(0.1, "bar")
    )
    res = material.extract_property(output)
    assert res == ans


class TestCoolPropsWrap(unittest.TestCase):
    def test_check(self):
        assert CoolPropsWrap.check("He")
        assert CoolPropsWrap.check("CarbonDioxide")
        assert CoolPropsWrap.check("Water")
        assert CoolPropsWrap.check("MyNewMat") == False
        Translator._data["MyNewMat"] = {"new_translate": {"name": "He"}}
        assert CoolPropsWrap.check("MyNewMat", translate_to="new_translate")


if __name__ == "__main__":
    unittest.main()
