import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

import numpy as np
import pint

# ----------Define Pint-----------#
# Disable Pint's old fallback behavior (must come before importing Pint)
os.environ["PINT_ARRAY_PROTOCOL_FALLBACK"] = "0"


ureg = pint.UnitRegistry()
Q_ = ureg.Quantity
ureg.define("displacements_per_atom = 1 = dpa = DPA")

# ----------Define Loggin-----------#
path = Path(f"{os.getcwd()}/base.log")
RotatingFileHandler(path, "a", maxBytes=5 * 1024 * 1024)

nice_format = logging.Formatter("%(message)s\n")
detailed_format = logging.Formatter(
    "%(asctime)s - %(levelname)s in %(module)s: %(message)s"
)

console = logging.StreamHandler()
console.setLevel(logging.ERROR)

console.setFormatter(detailed_format)

logging.getLogger("").addHandler(console)

run_log = logging.getLogger("run_log")

run_hand = logging.FileHandler(Path(path), "w")
run_hand.setLevel(logging.INFO)
run_hand.setFormatter(nice_format)
run_log.addHandler(run_hand)

logging.info("\n\n###\tInitialising Framework\t###\n")

from .base import BaseFramework, BaseConfig
from .bom import Assembly, Component, HomogenisedAssembly
from .parameters import MissingParamError


def update_config(new_config: BaseConfig):
    new_config.define_config(config_dict=BaseFramework._configuration.to_dict())
    BaseFramework._configuration = new_config
