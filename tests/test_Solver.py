from pathlib import Path
import unittest

import json

from bom_analysis import ureg
from bom_analysis.build import Framework
from bom_analysis.solver import Solver

config_path = "./tests/test_config.json"

with open(Path("./tests/test_settings.json"), "r") as f:
    SETTINGS = json.load(f)


class ToParams:
    def __init__(self):
        pass

    def generate(self, body):
        body.params.mass = 1.50 * ureg("g")


class ToNetwork:
    def __init__(self):
        pass

    def run(self, body):
        body.network.create_df(5, "i", "j", "k", "l")
        body.network.data.at["i", 2] = "foobar"


class ToOther:
    def __init__(self):
        pass

    def execute(self, body, batches, **kwargs):
        for key, val in kwargs.items():
            setattr(body, key, val)
        body.batches = batches
        setattr(body, "CAD", "some cad geometry")


class TestSolver(unittest.TestCase):
    """test for the Solver"""

    def test_build(self):
        """tests ordereddict is built correctly"""
        self.framework = Framework(config_path=config_path)
        self.populated = Framework.reader(self.framework.skeleton, settings=SETTINGS)
        sol = Solver()
        sol.build_from_settings(SETTINGS, self.populated)
        assert sol.run["fw_radial_build"].args[0].ref == "fw"
        assert (
            sol.run["mf_radial_build"].args[0].network.class_str[0]
            == "bom_analysis.base.DFClass"
        )

    def test_solve(self):
        """tests the solve is working correctly"""
        self.framework = Framework(config_path=config_path)
        self.populated = Framework.reader(self.framework.skeleton, settings=SETTINGS)
        sol = Solver()
        sol.build_from_settings(SETTINGS, self.populated)
        sol.solve()
        assert self.populated.fw.params.mass == 1.50 * ureg("g")
        assert self.populated.bz.network.data.at["i", 2] == "foobar"
        assert self.populated.bz.bz_breeder.CAD == "some cad geometry"

    def test_dual_load(self):
        """tests can load any kwargs/args from settings"""
        self.framework = Framework(config_path=config_path)
        self.populated = Framework.reader(self.framework.skeleton, settings=SETTINGS)

        SETTINGS["modules"]["bz_radial_build"] = {}
        info = SETTINGS["modules"]["bz_radial_build"]
        info["kwargs"] = {"faceting_tolerance": 0.1}
        sol = Solver()
        sol.build_from_settings(SETTINGS, self.populated)
        sol.solve()
        assert self.populated.bz.bz_breeder.batches == 5
        assert self.populated.bz.bz_breeder.number_of_particles == 100
        assert self.populated.bz.bz_breeder.faceting_tolerance == 0.1


if __name__ == "__main__":
    unittest.main()
