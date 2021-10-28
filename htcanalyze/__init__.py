"""htcanalyze module."""

import sys
import logging
from argparse import HelpFormatter


class CustomFormatter(HelpFormatter):
    """

    Custom formatter for setting argparse formatter_class.

    Identical to the default formatter,
     except that very long option strings are split into two
    lines.

    Solution discussed on: https://bit.ly/32CkCWK
    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts = []
        # if the Optional doesn't take a value, format is:
        #    -s, --long
        if action.nargs == 0:
            parts.extend(action.option_strings)
        # if the Optional takes a value, format is:
        #    -s ARGS, --long ARGS
        else:
            default = action.dest.upper()
            args_string = self._format_args(action, default)
            for option_string in action.option_strings:
                # parts.append('%s %s' % (option_string, args_string))
                parts.append(f"{option_string}, {args_string}")

        if sum(len(s) for s in parts) < self._width - (len(parts) - 1) * 2:
            return ', '.join(parts)
        # else
        return ',\n  '.join(parts)


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
