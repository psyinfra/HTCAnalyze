"""Global parameters."""

import os
from . import get_package_name

# --- Main Globals --- #
# config paths to watch in the following order
CONFIG_PATHS = [
    f"/etc/{get_package_name()}.conf",
    f"~/.config/{get_package_name()}.conf",
    f"{os.getcwd()}/config/{get_package_name()}.conf",
    f"{os.getcwd()}/{get_package_name()}.conf"
]

ALLOWED_SHOW_VALUES = [
    "htc-err",
    "htc-out"
]

EXT_LOG_DEFAULT = ".log"
EXT_OUT_DEFAULT = ".out"
EXT_ERR_DEFAULT = ".err"

# Exit Codes
NORMAL_EXECUTION = 0
NO_VALID_FILES = 1
ARGUMENT_ERROR = 2  # 2 is default by argparse
TYPE_ERROR = 3
KEYBOARD_INTERRUPT = 4

TOLERATED_USAGE = 0.1
BAD_USAGE = 0.25

# Errors can mess up the output, hence it's useful to reduce the number
# of errors. If there are more than just return a number
MAX_ERROR_LIMIT = 10

# HTCondor date format
STRP_FORMAT = "%Y-%m-%dT%H:%M:%S"
STRF_FORMAT = "%m-%d %H:%M:%S"
