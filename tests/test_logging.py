import unittest
import tempfile
import shutil

import pytest

from bom_analysis import run_log
from bom_analysis.utils import change_handler
from bom_analysis.base import BaseConfig

@pytest.mark.unittest
class LoggingTest(unittest.TestCase):
    def setUp(self):
        change_handler("./run.log")

    def tearDown(self):
        change_handler("./run.log")

    def test_debug(self):
        """tests the importing of run_log"""
        run_log.error("Appears Everywhere")
        run_log.info("Does not Appear on Console")
        run_log.debug("Only Appears in base.log")
        with open("./base.log", "r") as f:
            base_content = f.readlines()
        assert (
            base_content[-1][26::]
            == "DEBUG in test_logging: Only Appears in base.log\n"
        )

    def test_no_write_to_run(self):
        """tests after using a logging message will not appear in run log"""

        run_log.warning("Does not appear in console")
        run_log.info("Does not appear in console")

    def test_change_location(self):

        run_log.info("In ./run.log")
        with open("./run.log", "r") as f:
            content = f.readline()
        assert content == "INFO: In ./run.log\n"

        change_handler("./temp/run.log")

        run_log.info("In ./temp/run.log")
        with open("./temp/run.log", "r") as f:
            content = f.readline()
        assert content == "INFO: In ./temp/run.log\n"

    def test_change_location_config(self):
        run_log.info("Again in ./run.log")
        with open("./run.log", "r") as f:
            content = f.readlines()

        assert content[-2] == "INFO: Again in ./run.log\n"

        BaseConfig.temp_dir = "./temp/"

        run_log.info("Again in ./temp/run.log")
        with open("./temp/run.log", "r") as f:
            content = f.readlines()
        assert content[-2] == "INFO: Again in ./temp/run.log\n"
        with tempfile.TemporaryDirectory(prefix="temp_", dir="./temp/") as tmp_dir:
            BaseConfig.temp_dir = tmp_dir

            run_log.info("final test in a new dir")
            with open(f"{tmp_dir}/run.log", "r") as f:
                content = f.readlines()
            assert content[-2] == "INFO: final test in a new dir\n"
            BaseConfig.temp_dir = "./"
        with open("./temp/run.log", "r") as f:
            content = f.readlines()
            
        assert content[-2] == "INFO: Again in ./temp/run.log\n"


        with open("./base.log", "r") as f:
            base_content = f.readlines()
        assert base_content[-3][26::] == "INFO in test_logging: Again in ./run.log\n"
        assert (
            base_content[-2][26::] == "INFO in test_logging: Again in ./temp/run.log\n"
        )
        assert (
            base_content[-1][26::] == "INFO in test_logging: final test in a new dir\n"
        )


if __name__ == "__main__":
    unittest.main()
