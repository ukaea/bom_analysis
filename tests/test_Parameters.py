from logging import WARNING
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from box import Box
import json
import numpy as np
import pytest

from bom_analysis import ureg, Q_, run_log
from bom_analysis.base import BaseConfig
import bom_analysis.parameters as par

with open(Path("./tests/test_config.json"), "r") as f:
    CONFIG = json.load(f)


@pytest.mark.unittest
class TestFlexParam(unittest.TestCase):
    def test_flex_init(self):
        """probably not a unittest"""

        class UnsharedParam(par.FlexParam):
            pass

        test_1 = UnsharedParam(dict(var="hello", value="world"))
        test_2 = UnsharedParam(dict(var="hello", value="world", foo="bar"))
        np.testing.assert_array_equal(test_1._additional_keys, np.array(["foo"]))

        test_3 = UnsharedParam(Box(dict(var="hello", value="world", foo="bar")))

        assert test_3.foo == "bar"
        assert test_2.value == "world"
        assert test_1.var == "hello"

    def test_flex_fail(self):
        with self.assertRaises(KeyError):
            test_2 = par.FlexParam(dict(var="hello"))

    def test_check_inputs(self):
        test_1 = par.FlexParam(dict(var="hello", value="world"))
        test_1.check_inputs(dict(var="", value=""))
        test_1.check_inputs(Box(dict(var="", value="")))
        with self.assertRaises(KeyError):
            test_1.check_inputs(dict(hello=""))

        with self.assertRaises(KeyError):
            test_1.check_inputs((Box(dict(var="", hello=""))))

    def test_process_inputs(self):
        class UnsharedParam(par.FlexParam):
            _required_keys = np.array(["hello", "world"])
            _additional_keys = np.array(["foo"])

        processed = UnsharedParam.process_inputs(dict(hello="", world=""))
        self.assertDictEqual(processed, dict(hello="", world="", foo=None))

        processed = UnsharedParam.process_inputs(dict(hello="", world="", bar=""))
        self.assertDictEqual(processed, dict(hello="", world="", foo=None, bar=""))

        processed = UnsharedParam.process_inputs(dict(hello="", world=""))
        self.assertDictEqual(processed, dict(hello="", world="", foo=None, bar=None))

    def test_update(self):
        class UnsharedParam(par.FlexParam):
            _required_keys = np.array(["var", "value"])
            _additional_keys = np.array([])

        test_1 = UnsharedParam(dict(var="hello", value="world"))
        test_2 = UnsharedParam(dict(var="hello", value="world", foo="bar"))
        assert test_1.foo is None

    def test_parameter(self):
        test_1 = par.FlexParam(dict(var="hello", value="world"))
        box_data = test_1.parameter()
        self.assertDictEqual(box_data.to_dict(), dict(var="hello", value="world"))

    def test_asdict(self):
        test_1 = par.FlexParam(dict(var="hello", value="world"))
        output = test_1.asdict()
        self.assertDictEqual(output, dict(var="hello", value="world"))

    def test_repr(self):
        test_1 = par.FlexParam(dict(var="hello", value="world"))
        print(test_1)

    def test_replace(self):
        class UnsharedParam(par.FlexParam):
            _required_keys = np.array(["var", "value"])
            _additional_keys = np.array([])

        test_1 = UnsharedParam(dict(var="hello", value="world"))
        test_1.replace(value="foo")
        assert test_1.value == "foo"
        self.assertDictEqual(test_1.asdict(), dict(var="hello", value="foo"))
        test_1.replace(foo="bar")
        assert test_1.foo == "bar"

        test_2 = UnsharedParam(dict(var="hello", value="world", a=""))
        test_2.replace(a="b")
        assert test_2.a == "b"

    def test_fields(self):
        class UnsharedParam(par.FlexParam):
            _required_keys = np.array(["var", "value"])
            _additional_keys = np.array(["foo", "bar"])

        test = UnsharedParam(dict(var="hello", value="world"))
        np.testing.assert_array_equal(
            test.fields, np.array(["var", "value", "foo", "bar"])
        )

    def test_check_for_pint(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m")))
        assert test_2.unit == "meter"
        test_2.check_for_pint(dict(var="hello", value=Q_(1, "mile")))

    def test_check_non_string(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m")))

        with self.assertRaises(ValueError):
            test_2.check_non_string(dict(var="hello", value=1.0))

        data = dict(value=Q_(1.0, "cm"))
        test_2.check_non_string(data)

        assert data["unit"] == "centimeter"

        data_2 = dict(value=4.0, unit="m")
        test_2.check_non_string(data_2)
        assert data_2["value"] == Q_(4, "m")

        test_3 = par.PintParam(dict(var="hello", value=Q_(1)))
        data_3 = dict(value=4.0, unit=None)
        test_3.check_non_string(data_3)
        assert data_3["value"] == Q_(4)

    def test_check_dimensionality(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m"), unit="m"))

        with self.assertRaises(AssertionError):
            test_2.check_dimensionality(dict(value=Q_(1, "m"), unit="s"))

    def test_check_for_pint(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m")))

        with self.assertRaises(ValueError):
            test_2.check_for_pint(dict(var="hello", value=1.0))

        with self.assertRaises(AssertionError):
            test_2.check_for_pint(dict(value=Q_(1.0, "s")))

    def test_check_string(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m")))

        test_2.check_string(dict(value="hello"))

        example_input = dict(value="1 m")
        test_2.check_string(example_input)
        assert example_input["value"] == Q_(1, "m")

    def test_none_input(self):
        par.PintParam(dict(var="mass", value=None))

    def test_json(self):
        test_2 = par.PintParam(dict(var="hello", value=Q_(1, "m")))

        dump = test_2.asdict()
        serialisable = json.dumps(dump)
        assert dump["value"] == 1.0
        assert dump["unit"] == "meter"

    def test_asdict_None(self):
        test_1 = par.PintParam(dict(var="hello", value=Q_(1)))

        dump = test_1.asdict()
        assert dump["unit"] == "dimensionless"

        test_2 = par.PintParam(dict(var="hello", value=1, unit=None))

        dump = test_2.asdict()
        assert dump["unit"] == "dimensionless"

        test_3 = par.PintParam(dict(var="hello", value="world"))

        dump = test_3.asdict()
        assert dump["unit"] == "dimensionless"

    def test_nones(self):
        test_1 = par.PintParam(dict(var="hello", value=None, unit=None))
        test_2 = par.PintParam(dict(var="hello", value=None, unit="kg"))
        test_3 = par.PintParam(dict(var="hello", value=10, unit=None))
        test_4 = par.PintParam(dict(var="hello", value=10, unit="None"))
        test_5 = par.PintParam(dict(var="hello", value="None", unit="m"))


@pytest.mark.integrationtest
class TestParameterFrameStandalone(unittest.TestCase):
    def test_getattr(self):
        class UnsharedParam(par.FlexParam):
            pass

        pf = par.ParameterFrame()
        pf._data["mass"] = UnsharedParam(dict(value=1, var="mass", deviation=0.1))
        assert pf.mass == 1
        assert pf.get_param("mass", "deviation") == 0.1

    def test_check_param(self):
        pf = par.ParameterFrame()
        pf._data["mass"] = MagicMock()
        assert pf.check_param("mass")
        assert not pf.check_param("volume")

    def test_when_param_not_in_data(self):
        pf = par.ParameterFrame()
        with self.assertRaises(par.MissingParamError):
            pf.mass

        with self.assertRaises(par.MissingParamError):
            pf.get_param("mass")

    def test_iter(self):
        pf = par.ParameterFrame()
        pf._data["mass"] = par.FlexParam(dict(value=1, var="mass"))
        pf._data["volume"] = par.FlexParam(dict(value=2, var="volume"))
        pf._data["tbr"] = par.FlexParam(dict(value=3, var="tbr"))
        output_list = [param.value for param in pf]
        self.assertCountEqual(output_list, [1, 2, 3])

    def test_order(self):
        pf = par.ParameterFrame()
        pf._data["mass"] = par.FlexParam(dict(value=1, var="mass"))
        pf._data["volume"] = par.FlexParam(dict(value=2, var="volume"))
        pf._data["tbr"] = par.FlexParam(dict(value=3, var="tbr"))
        np.testing.assert_array_equal(pf.order, np.array(["mass", "volume", "tbr"]))

    def test_header(self):
        class UnsharedParam(par.FlexParam):
            pass

        pf = par.ParameterFrame()
        pf._data["mass"] = UnsharedParam(dict(value=1, var="mass", foo=""))
        pf._data["volume"] = UnsharedParam(dict(value=2, var="volume", bar=""))
        pf._data["tbr"] = UnsharedParam(dict(value=3, var="tbr", source=None))
        self.assertCountEqual(pf.header, ["var", "value", "foo", "bar", "source"])

    def test_add_parameter(self):
        pf = par.ParameterFrame()
        pf.add_parameter(var="mass", value=1, source="hello")
        assert pf.mass == 1

        pf.add_parameter(source="hello", var="volume", value=2)
        assert pf.volume == 2

    def test_set_attr(self):
        pf = par.ParameterFrame()
        BaseConfig.restrict_param = False
        pf.mass = 1
        BaseConfig.restrict_param = True
        with self.assertRaises(par.MissingParamError):
            pf.volume = 2

        pf._data["tbr"] = par.FlexParam(dict(var="tbr", value=3))
        pf.tbr = 5
        assert pf.mass == 1
        with self.assertRaises(par.MissingParamError):
            volume = pf.volume
        assert pf.tbr == 5

    def test_get_param(self):
        pf = par.ParameterFrame()
        pf.add_parameter(var="mass", value=1, source="hello")
        mass = pf.get_param("mass")
        assert mass.source == "hello"
        mass_value = pf.get_param("mass", "value")
        assert mass_value == 1

        with self.assertRaises(par.MissingParamError):
            pf.get_param("volume")

    def test_extract_dictionary_of_parameters(self):
        pf = par.ParameterFrame()
        ans = pf.convert_parameter_dictionary_to_list({"mass": Q_(1, "kg")})
        self.assertDictEqual(ans[0], {"var": "mass", "value": Q_(1, "kg")})
        with self.assertLogs(run_log, WARNING):
            pf.convert_parameter_dictionary_to_list(
                {"volume": {"var": "mass", "value": Q_(1, "kg")}}
            )

    def test_new_line_in_string(self):
        pf = par.ParameterFrame()
        ans = pf.new_line_in_string("hello", 1)
        assert ans == "h\ne\nl\nl\no"

    @unittest.expectedFailure
    def test_no_float_int_input(self):
        pf = par.PintFrame()
        pf.add_parameter(var="mass", value=Q_(1, "kg"), source="hello")
        pf.mass = 2

    @unittest.expectedFailure
    def test_adding_directly(self):
        BaseConfig.restrict_param = False
        pf = par.PintFrame()
        pf.configuration = "up-down"
        pf.mass = Q_(1000, "tonnes")
        pf.add_parameter(
            name="major_radius",
            quantity=Q_(2, "m"),
            description="a major radius of a torus",
        )
        BaseConfig.restrict_param = True


@pytest.mark.unittest
class TestParameterFrame(unittest.TestCase):
    def test_default_from_dict(self):
        example = {"params": {"data": {"volume": {"value": 200, "unit": "m**3"}}}}
        params = par.PintFrame()
        out = params.default_from_dict(example)
        self.assertDictEqual(out[0], dict(var="volume", value=200, unit="m**3"))

    def test_default_from_dict_no_params(self):
        example = {"data": {"volume": {"value": 200, "unit": "m**3"}}}
        params = par.PintFrame()
        out = params.default_from_dict(example)
        self.assertDictEqual(out[0], dict(var="volume", value=200, unit="m**3"))

    def test_default_from_dict_no_data(self):
        example = {"volume": {"value": 200, "unit": "m**3"}}
        params = par.PintFrame()
        out = params.default_from_dict(example)
        self.assertDictEqual(out[0], dict(var="volume", value=200, unit="m**3"))

    def test_default_from_dict_mistake(self):
        example = {"data": {"mass": {"var": "volume", "value": 200, "unit": "m**3"}}}
        params = par.PintFrame()
        with self.assertLogs(run_log, WARNING):
            out = params.default_from_dict(example)

    @patch("bom_analysis.parameters.PintFrame.default_from_dict")
    def test_add_defaults(self, dfd):
        BaseConfig.restrict_param = True
        dfd.return_value = [
            dict(var="volume", value=200, unit="m**3"),
            dict(var="mass", value=200000, unit="kg"),
        ]
        params = par.PintFrame()
        params._data["mass"] = par.PintParam(dict(var="mass", value=None))
        params._data["volume"] = par.PintParam(dict(var="volume", value=None))
        params.add_defaults({})
        assert params.volume.m == 200
        assert params.mass.m == 200000

    @patch("bom_analysis.parameters.PintFrame.default_from_dict")
    def test_add_defaults_if_exists(self, dfd):
        dfd.return_value = [
            dict(var="volume", value=200, unit="m**3"),
            dict(var="mass", value=200000, unit="kg"),
        ]
        params = par.PintFrame()
        params._data["mass"] = par.PintParam(
            dict(var="volume", value=Q_(100000, "g"), unit="g")
        )
        params._data["volume"] = par.PintParam(
            dict(var="volume", value=Q_(100, "cm**3"), unit="cm**3")
        )
        params.add_defaults({})
        assert params.volume.to("m**3").m == 200
        assert params.mass.to("kg").m == 200000

    def test_no_unit(self):
        params = par.PintFrame()
        params._data["foo"] = par.PintParam(
            dict(var="foo", value=Q_("bar", ""), unit=None)
        )
        params._data["volume"] = par.PintParam(
            dict(var="volume", value=Q_(100, "cm**3"), unit="cm**3")
        )
        assert params.to_dict()["data"]["foo"]["unit"] == "dimensionless"

    @patch("bom_analysis.parameters.PintFrame.default_from_dict")
    def test_no_unit_in(self, dfd):
        dfd.return_value = [dict(var="volume", value=200, unit="dimensionless")]
        params = par.PintFrame()
        params.from_dict({})
        assert str(params.volume.units) == "dimensionless"


@pytest.mark.integrationtest
class TestParameters(unittest.TestCase):
    """test for the framework"""

    def setUp(self):
        """sets up test"""
        with open(Path(CONFIG["parameters"]["location"][0]), "r") as f:
            self.data = json.load(f)
        # self.populated = Framework.reader(SETTINGS, skel)

    def test_FlexParam(self):
        """tests the top level of the assembly"""
        param = self.data["component"]["volume"]
        ParamTuple = par.FlexParam(param)
        a = ParamTuple.data
        assert a.name == "Component Volume"

    def test_ParameterFrame(self):
        """tests a full parameter frame"""
        pf = par.ParameterFrame(data=self.data["component"])
        pf.from_dict({"data": self.data["component"]})
        assert pf.get_param("thickness", key="unit") == "m"

    def test_VariableParameterFrame(self):
        """tests a variable parameter frame in which an
        entry can be given additional keys"""
        extra_s = {"var": "extra_s", "value": None}
        extra_l = {
            "var": "extra_l",
            "value": None,
            "unit": "T",
            "descr": None,
            "name": "extra large",
            "source": "made up",
            "foo": "bar",
        }
        self.data["component"]["small"] = extra_s
        self.data["component"]["large"] = extra_l
        pf = par.ParameterFrame(data=self.data["component"])
        pf.from_dict({"data": self.data["component"]})
        assert pf.get_param("extra_s", key="unit") is None
        assert pf.get_param("thickness", key="foo") is None
        par.FlexParam._additional_keys = np.array([])

    def test_TestInput(self):
        """test the values are being set correctly"""
        data = self.data["component"]
        data["mass"]["value"] = 100.0
        data["volume"]["value"] = "who knows"
        pf = par.ParameterFrame(data=data)
        pf.from_dict({"data": self.data["component"]})
        pf.thickness = 20
        assert pf.thickness == 20
        assert pf.volume == "who knows"
        assert pf.mass == 100.0

    def test_add_parameter(self):
        pf = par.ParameterFrame()
        pf.add_parameter(var="length", value=1, hello="world")
        assert pf.length == 1

    def test_int_or_float(self):
        pf = par.ParameterFrame()
        pf.add_parameter(var="length", value=1, hello="world")
        pf.length = 1.0

    def test_empty_print(self):
        pf = par.ParameterFrame()
        print(pf)


@pytest.mark.integrationtest
class TestPintameters(unittest.TestCase):
    """test for the framework"""

    def setUp(self):
        """sets up test"""
        with open(Path(CONFIG["parameters"]["location"][0]), "r") as f:
            self.data = json.load(f)
        # self.populated = Framework.reader(SETTINGS, skel)

    def test_PintParam(self):
        """tests the top level of the assembly"""
        param = self.data["component"]["volume"]
        ParamTuple = par.PintParam(param)
        a = ParamTuple.parameter()
        assert a.name == "Component Volume"

    def test_VariablePintFrame(self):
        """tests a variable parameter frame in which an
        entry can be given additional keys"""
        extra_s = {"var": "extra_s", "value": None, "unit": None}
        extra_l = {
            "var": "extra_l",
            "value": None,
            "unit": "T",
            "descr": None,
            "name": "extra large",
            "source": "made up",
            "foo": "bar",
        }
        self.data["component"]["small"] = extra_s
        self.data["component"]["large"] = extra_l
        pf = par.PintFrame(data=self.data["component"])
        pf.from_dict({"data": self.data["component"]})
        assert pf.get_param("extra_s", key="unit") is None
        assert pf.get_param("thickness", key="foo") is None

    def test_PintFrame(self):
        """tests a full parameter frame"""
        pf = par.PintFrame(data=self.data["component"])
        pf.from_dict({"data": self.data["component"]})
        assert pf.get_param("thickness", key="unit") == "m"

    # @unittest.expectedFailure
    # def test_TestFailInput(self):
    #     """check you cannot give a non pint value when there
    #     is a unit"""
    #     data = self.data["component"]
    #     pf = par.PintFrame(data=data)
    #     pf.from_dict({"data":self.data["component"]})
    #     pf.thickness = 20

    @unittest.expectedFailure
    def test_TestWrongDimension(self):
        """check you cannot give a non pint value when there
        is a unit"""
        data = self.data["component"]
        pf = par.PintFrame(data=data)
        pf.from_dict({"data": self.data["component"]})
        print(pf.get_param("thickness"))
        pf.thickness = 20 * ureg("m**3")

    def test_TestInput(self):
        """test the values are being set correctly"""
        data = self.data["component"]
        data["mass"]["value"] = 100.0
        data["volume"]["value"] = "who knows"
        pf = par.PintFrame(data=data)
        pf.from_dict({"data": self.data["component"]})
        pf.thickness = 20 * ureg("m")
        assert pf.thickness == 20 * ureg("m")
        assert pf.volume == "who knows" * ureg("m**3")
        assert pf.mass == 100.0 * ureg("kg")

    def test_dump(self):
        """tests that parameters can be correctly dumped to json"""
        data = self.data["component"]
        data["mass"]["value"] = np.array([100.0])[0]
        data["mass"]["unit"] = None
        data["volume"]["value"] = np.array([200.0])[0]
        pf = par.PintFrame(data=data)
        pf.from_dict({"data": self.data["component"]})
        pf.thickness = 20 * ureg("m")
        dump = pf.to_dict()

    def test_add_parameter(self):
        pf = par.PintFrame()
        pf.add_parameter(var="length", value=Q_(1, "m"), hello="world")
        assert pf.length.m == 1
        dump = pf.to_dict()


@pytest.mark.regressiontest
class TestPintQOL(unittest.TestCase):
    """regresssion test for the removal of annoying
    pint units such as mm/cm instead of dimensionless"""

    def setUp(self):
        self.params = par.PintFrame()

    def test_length_dimensionless(self):
        dat = {
            "len1": {"var": "len1", "value": 1, "unit": "m"},
            "len2": {"var": "len2", "value": 1, "unit": "cm"},
        }
        self.params.from_dict({"data": dat})

        should_be_dimensionless = self.params.len1 / self.params.len2
        should_be_dimensionless = should_be_dimensionless.to_reduced_units()
        assert str(should_be_dimensionless.units) == "dimensionless"
        assert should_be_dimensionless.magnitude == 100

    def test_skeleton_dimensionless(self):
        dat = {
            "len1": {"var": "len1", "value": 1, "unit": "m"},
            "len2": {"var": "len2", "value": 1, "unit": "cm"},
            "should_be_dimensionless": {
                "var": "should_be_dimensionless",
                "value": 100,
                "unit": None,
            },
        }
        self.params.from_dict({"data": dat})
        self.params.should_be_dimensionless = self.params.len1 / self.params.len2
        param_dict = self.params.to_dict()["data"]
        assert param_dict["should_be_dimensionless"]["value"] == 100.0
        assert param_dict["should_be_dimensionless"]["unit"] == "dimensionless"


@pytest.mark.integrationtest
class TestPrintingOfFrames(unittest.TestCase):
    def test_default_from_dict_no_data(self):
        example = {"volume": {"value": 200, "unit": "m**3", "source": "madeup"}}
        params = par.PintFrame()
        params.from_dict(example)
        print(params)

    def test_default_from_dict_no_data_long(self):
        example = {"volume": {"value": 1 / 3, "unit": "m**3", "source": "madeup"}}
        params = par.PintFrame()
        params.from_dict(example)
        print(params)

    def test_default_from_dict_long_unit(self):
        example = {
            "volume": {
                "value": 1 / 3,
                "unit": "meter**3/kilograms*megajoules",
                "source": "madeup",
            }
        }
        params = par.PintFrame()
        params.from_dict(example)

        print(params)

    def test_default_from_dict_long_desc(self):
        example = {
            "volume": {
                "value": 1 / 3,
                "unit": "m**3",
                "source": "madeup",
                "name": (
                    "This is a rather long description that might look better if it is wrapped a bit "
                    "This is a rather long description that might look better if it is wrapped a bit"
                ),
            }
        }
        params = par.PintFrame()
        params.from_dict(example)
        print(params)


if __name__ == "__main__":
    unittest.main()
