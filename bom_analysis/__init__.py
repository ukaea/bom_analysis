import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Any, Callable, Type

import pint

# Pint
# Disable Pint's old fallback behavior (must come before importing Pint)
os.environ["PINT_ARRAY_PROTOCOL_FALLBACK"] = "0"
ureg = pint.UnitRegistry()
Q_: Type[pint.Quantity] = ureg.Quantity
ureg.define("displacements_per_atom = 1 = dpa = DPA")

# Create Logger
run_log = logging.getLogger("bom_analysis_log")
run_log.setLevel(logging.DEBUG)

# Log Formats
nice_format = logging.Formatter("%(levelname)s: %(message)s\n")
detailed_format = logging.Formatter(
    "%(asctime)s - %(levelname)s in %(module)s: %(message)s"
)

# Base Logging - Captures Everything with Time Stamp, written to current working directory
path = Path(f"{os.getcwd()}/base.log")
base_handler = RotatingFileHandler(path, "a", maxBytes=5 * 1024 * 1024)
base_handler.setLevel(logging.DEBUG)
base_handler.setFormatter(detailed_format)

# Console Logging - Displays Errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(detailed_format)

# Run Log - Displays Information about a Run, written to current temporary directory
info_path = Path(f"{os.getcwd()}/run.log")
info_handler = logging.FileHandler(info_path, "w")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(nice_format)

# Add Handlers to Log
run_log.addHandler(base_handler)
run_log.addHandler(console_handler)
run_log.addHandler(info_handler)

from .base import BaseFramework, BaseConfig
from .bom import Assembly, Component, HomogenisedAssembly
from .parameters import MissingParamError


def update_config(new_config: Type[BaseConfig]):
    """Updates the configuration within the Framework
    class.

    Using the framework in this way allows a new configuration
    to be supplied to the bom_analysis classes as they take the
    Configuration from the Framework instead of the BaseConfig.


    Parameters
    ----------
    new_config : BaseConfig
        A configuration class that will be used by bom_analysis.
    """
    new_config.define_config(config_dict=BaseFramework._configuration.to_dict())
    BaseFramework._configuration = new_config
