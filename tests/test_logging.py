import logging
import os
from pathlib import Path
import unittest

from bom_analysis import nice_format, run_log

run_hand = logging.FileHandler(Path(f"{os.getcwd()}/run.log"), "w")
run_hand.setLevel(logging.INFO)
run_hand.setFormatter(nice_format)
run_log.addHandler(run_hand)


class LoggingTest(unittest.TestCase):
    def test_log(self):
        """tests console write"""
        logging.debug("Don't Appear on Console, debug")
        logging.info("Don't Appear on Console, info")
        logging.warning("Don't Appear on Console, warning")
        logging.error("Appear on Console, error")

    def test_import_log(self):
        """tests the importing of run_log"""
        from bom_analysis import run_log

        run_log.error("Appear on Console, run_log, base_log, error")
        run_log.info("Appear on run_log, base_log, info")
        run_log.debug("Appear on base_log, debug")

    def test_no_write_to_run(self):
        """tests after using a logging message will not appear in run log"""
        from bom_analysis import run_log

        run_log.warning("Appear on base_log, run_log, warning")
        logging.info("Appear on base, Please Don't Appear in Run, info")

    def test_change_location(self):
        from bom_analysis import run_log

        run_log.warning("should only appear in run_log in cwd")

        from bom_analysis import nice_format

        for hdlr in run_log.handlers[:]:
            run_log.removeHandler(hdlr)
        run_hand = logging.FileHandler(Path(f"{os.getcwd()}/tests/run.log"), "w")
        run_hand.setLevel(logging.INFO)
        run_hand.setFormatter(nice_format)
        run_log.addHandler(run_hand)

        run_log.warning("should only appear in tests/run_log")
        run_log.warning("but everything should appear in base log")

    @unittest.expectedFailure
    def test_assert_in_log(self):
        """tests failed asserts go to log"""
        a = 1
        assert a == 2, "would like assert to go to log"

    @unittest.expectedFailure
    def test_value_error(self):
        """tests failed asserts go to log"""
        raise ValueError("ValueError to log?")


if __name__ == "__main__":

    def timed():
        Framework(CONFIG)

    unittest.main()
