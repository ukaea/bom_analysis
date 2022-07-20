import copy
import unittest

from bom_analysis import Q_
from bom_analysis.utils import UpdateDict, Translator, access_nested, PrintParamsTable


class TestMerge(unittest.TestCase):
    """test for the framework"""

    def test_integer(self):
        """test that simple integer dict can be merged"""
        a = {"a": 10, "b": 20}
        b = {"c": 30, "d": 40}
        c = {"x": 1}
        ans = {"a": 10, "b": 20, "c": 30, "d": 40, "x": 1}
        ud = UpdateDict(a, b, c)
        self.assertDictEqual(ud.main, ans)

    def test_string(self):
        """tests basic string"""
        a = {"a": "hello", "b": "foo"}
        b = {"b": "bar"}
        ud = UpdateDict(a, b)
        assert a["b"] == "bar"

    def test_nested_string(self):
        """tests a nested string"""
        a = {"a": "hello"}
        b = {"world": {"foo": "bar", "test_name": "test_param"}}
        c = {"world": {"test_name": "other_test_param"}}
        ans = {"a": "hello", "world": {"foo": "bar", "test_name": "other_test_param"}}
        ud = UpdateDict(a, b, c)
        self.assertDictEqual(ud.main, ans)

    def test_order(self):
        """tests the order of the dictionary does not matter"""
        parts = {
            "assembly": {
                "class_str": ["bom_analysis.bom.Assembly"],
                "params_name": ["assembly"],
            },
            "component": {
                "class_str": ["bom_analysis.bom.Component"],
                "params_name": ["component"],
            },
        }
        tokamak_parts = {
            "blanket": {
                "inherits": ["assembly"],
                "children": {
                    "breeding_zone": {"type": "breeding_pins"},
                    "manifold": {"type": "double_wall_mf"},
                },
            },
            "breeding_pins": {"inherits": ["component"]},
            "double_wall_mf": {"inherits": ["component"]},
        }
        parts2 = copy.deepcopy(parts)
        tokamak_parts2 = copy.deepcopy(tokamak_parts)
        UpdateDict(parts, tokamak_parts)
        UpdateDict(tokamak_parts2, parts2)
        assert parts == tokamak_parts2


class TestTranslator(unittest.TestCase):
    def setUp(self):
        Translator.define_translations(["./examples/files/translation.json"])

    def test_translate(self):
        new = Translator("H2O", "CoolProps")
        assert new == "Water"


class TestFunctions(unittest.TestCase):
    def test_access_dict(self):
        a = {"foo": {"bar": {"hello": "world"}}}
        b = access_nested(a, ["foo", "bar", "hello"])
        assert b == "world"

    def test_access_class(self):
        class c:
            def __init__(self):
                self.bar = {"hello": "world"}

        a = {"foo": c()}
        b = access_nested(a, ["foo", "bar", "hello"])
        assert b == "world"

    def test_access_class(self):
        class c:
            def __init__(self):
                self.bar = {"hello": "world"}

        a = {"foo": c()}
        b = access_nested(a, ["foo", "None_please", "hello"])
        assert b is None


class TestPrintParamsTable(unittest.TestCase):
    def test_shorten_unit(self):
        ppt = PrintParamsTable()
        assert ppt.shorten_unit("hello") == "hello"
        assert ppt.shorten_unit(12345.6) == 12345.6
        assert ppt.shorten_unit(12345) == 12345
        assert ppt.shorten_unit(None) == None
        assert ppt.shorten_unit(Q_("1000 meter*kilogram")) == "1000 kg * m"

    def test_header_not_implemented(self):
        ppt = PrintParamsTable()
        with self.assertRaises(NotImplementedError):
            ppt.header

if __name__ == "__main__":
    unittest.main()
