"""htcanalyze module."""

import sys
import logging


def setup_logging_tool(verbose_mode):
    """
        Set up the logging device.

        to generate a log file, with --generate-log-file
        or to print more descriptive output with the verbose mode to stdout

        both modes are compatible together
    :return:
    """
    # disable the logging tool by default
    logging.getLogger().disabled = True

    # I don't know why a root handler is already set,
    # but we have to remove him in order
    # to get just the output of our own handler
    if len(logging.root.handlers) == 1:
        default_handler = logging.root.handlers[0]
        logging.root.removeHandler(default_handler)

    if verbose_mode:
        # activate logger if not already activated
        logging.getLogger().disabled = False

        logging_stdout_format = '%(asctime)s - %(levelname)s: %(message)s'
        stdout_formatter = logging.Formatter(logging_stdout_format)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(stdout_formatter)
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log.addHandler(stdout_handler)


def get_package_name():
    """Return package name."""
    return __name__
