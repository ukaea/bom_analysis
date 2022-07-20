import copy
from pathlib import Path
import unittest
from unittest.mock import MagicMock

import json
import pytest

from bom_analysis import Q_, ureg
from bom_analysis.base import BaseConfig as Config
from bom_analysis.build import Framework
from bom_analysis.bom import Assembly, Component
from bom_analysis.solver import Step, Solver

config_path = "./tests/test_config.json"

with open(Path("./tests/test_settings.json"), "r") as f:
    SETTINGS = json.load(f)


class TestLoad(unittest.TestCase):
    def test_load(self):
        """tests a skeleton can be loaded only from file and top"""
        Framework(config_path=config_path)
        with open("./tests/default_skeleton.json", "r") as f:
            skeleton = json.load(f)
        # pprint.pprint(skeleton)
        blanket = Framework.reader(skeleton, top="blanket")


class TestFramework(unittest.TestCase):
    """test for the framework"""

    def setUp(self):
        """sets up test"""

    def test_config_build(self):
        """tests the top level of the assembly"""
        self.framework = Framework(config_path=config_path)
        skel = copy.deepcopy(self.framework.skeleton)
        self.populated = Framework.reader(skel, settings=SETTINGS)
        assembly = Assembly()

        assembly.from_dict(self.framework.skeleton, ref=Config.top["ref"])

    def test_solve(self):
        """tests whether the a function can solve correctly"""
        self.framework = Framework(config_path=config_path)
        skel = copy.deepcopy(self.framework.skeleton)
        self.populated = Framework.reader(skel, settings=SETTINGS)
        self.solver = Framework.solver(SETTINGS, self.populated)
        self.solver.solve()
        with open("./tests/default_skeleton.json", "w") as f:
            json.dump(self.populated.to_dict(), f, indent=4, sort_keys=True)
        assert self.populated.fw.params.mass == 1.50 * ureg("g")
        assert self.populated.bz.network.data.at["i", 2] == "foobar"
        assert self.populated.bz.bz_breeder.CAD == "some cad geometry"


class Driving:
    def overtake(self, car):
        car.params.speed += Q_(10, "kph")


class Comfort:
    def turn_radio_on(self, radio, channel=None):
        radio.params.power = "on"
        radio.params.channel = channel

    def turn_radio_off(self, radio):
        radio.params.power = "off"


@pytest.mark.integrationtest
class TestClassBasedFramework(unittest.TestCase):
    def setUp(self):
        self.car = Assembly(ref="yaris")
        radio = Component(ref="radio")
        engine = Component(ref="electric_engine")
        self.car.add_components([radio, engine])

        self.car.params = MagicMock()
        self.car.params.speed = Q_(100, "kph")
        radio.params = MagicMock()
        engine.params = MagicMock()

    def tearDown(self):
        Framework._solver = Solver()

    def test_playing_with_radio(self):
        framework = Framework()
        radio_on = Step(Comfort, "turn_radio_on", self.car.radio)
        solver = framework.solver()
        solver.build_from_step_list([radio_on])
        solver.solve()
        assert self.car.radio.params.power == "on"

    def test_turn_off_radio_and_overtake(self):
        framework = Framework()
        radio_off = Step(Comfort, "turn_radio_off", self.car.radio)
        overtake = Step(Driving, "overtake", self.car)
        solver = framework.solver()
        solver.build_from_step_list([radio_off, overtake])
        solver.solve()
        assert self.car.radio.params.power == "off"
        assert self.car.params.speed == Q_(110, "kph")

    def test_settings(self):
        framework = Framework()
        radio_on = Step(
            Comfort, "turn_radio_on", self.car.radio, channel="bbc_world_service"
        )
        radio_off = Step(Comfort, "turn_radio_off", self.car.radio)
        solver = framework.solver()
        solver.build_from_step_list([radio_on, radio_off])
        solver.solve()
        settings = solver.to_dict()
        assert settings["order"]["1"] == "Comfort.turn_radio_off"
        self.assertDictEqual(
            settings["details"]["Comfort.turn_radio_on"],
            dict(
                class_str="tests.test_Framework.Comfort",
                run="turn_radio_on",
                args=["radio"],
                kwargs={"channel": "bbc_world_service"},
            ),
        )


if __name__ == "__main__":
    unittest.main()
