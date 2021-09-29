"""Global parameters."""

import sys
from htcanalyze import get_package_name

# --- Main Globals --- #
# config paths to watch in the following order
CONFIG_PATHS = [
    f'/etc/{get_package_name()}.conf',
    f'~/.config/{get_package_name()}.conf',
    f'{sys.prefix}/config/{get_package_name()}.conf'
]

ALLOWED_SHOW_VALUES = ["htc-err", "htc-out"]
ALLOWED_IGNORE_VALUES = [
    "execution-details", "times", "host-nodes", "used-resources",
    "requested-resources", "allocated-resources", "all-resources",
    "errors", "ram-history"
]

NORMAL_EXECUTION = 0
NO_VALID_FILES = 1
HTCANALYZE_ERROR = 2
TYPE_ERROR = 3
KEYBOARD_INTERRUPT = 4

# --- Resource Globals --- #

LEVEL_COLORS = {
    'error': 'red',
    'warning': 'yellow',
    'light_warning': 'yellow2',
    'normal': 'green'
}

# --- Display Globals --- #

# Errors can mess up the output, hence it's useful to reduce the number
# of errors. If there are more than just return a number
MAX_ERROR_LIMIT = 10

# --- JobDetails Globals --- #

STATE_COLORS = {
    'abnormal': 'red',
    'aborted': 'red',
    'error_while_reading': 'red',
    'normal': 'green',
    'waiting': 'blue',
    'executing': 'blue',
    'strange': 'red',
    'unknown': 'yellow'
}
