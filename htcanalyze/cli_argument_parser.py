
from configargparse import ArgumentParser
from argparse import HelpFormatter
from .globals import (
    CONFIG_PATHS,
    ALLOWED_IGNORE_VALUES,
    ALLOWED_SHOW_VALUES,
    EXT_LOG_DEFAULT,
    EXT_OUT_DEFAULT,
    EXT_ERR_DEFAULT,
    TOLERATED_USAGE,
    BAD_USAGE
)


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


class CLIArgumentParser(ArgumentParser):

    _ignore_configs = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignore_configs = False

    def set_default_config_paths(self, config_paths):
        self._default_config_files = config_paths

    def ignore_configs(self):
        """Mainly for testing, ignore configs every time"""
        self._ignore_configs = True

    def get_params(self, args=None):
        if args is None:
            args = []
        # add config paths if help wanted
        if "-h" in args or "--help" in args:
            self.set_default_config_paths(CONFIG_PATHS)
            self.parse_args(["-h"])
            # exit

        # else check if --ignore-config is set
        prio_args = self.parse_args(args)
        if not prio_args.ignore_config and not self._ignore_configs:
            # if not set add config paths
            self.set_default_config_paths(CONFIG_PATHS)

        return self.parse_args(args)


def setup_parser() -> CLIArgumentParser:
    """
    Define parser with all arguments listed below.

    :return: parser
    """

    parser = CLIArgumentParser(
        formatter_class=CustomFormatter,
        # Todo: Change when fixed:
        #       https://github.com/bw2/ConfigArgParse/issues/217
        allow_abbrev=False,
        description="Analyze or summarize HTCondor-Joblogs",
    )

    parser.add_argument(
        "paths",
        nargs="*",
        help="Directory of file paths for log files"
    )
    # also to add files with different destination,
    # to be used for config file / escaping flags with action=append
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=False,
        help="Recursive search through directory hierarchy"
    )

    parser.add_argument(
        "--version",
        help="Print out extended execution details",
        action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Print out extended execution details",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        default=False,
        help="Analyze given files one by one"
    )
    parser.add_argument(
        "--ext-log",
        help="Suffix of HTCondor job logs (default: none)",
        default=EXT_LOG_DEFAULT
    )
    parser.add_argument(
        "--ext-out",
        help="Suffix of job out logs (default: .out)",
        default=EXT_OUT_DEFAULT
    )
    parser.add_argument(
        "--ext-err",
        help="Suffix of job error logs (default: .err)",
        default=EXT_ERR_DEFAULT
    )

    ignore_metavar = (
            "{" + ALLOWED_IGNORE_VALUES[0] + ", ... }"
    )
    allowed_ign_vals = ALLOWED_IGNORE_VALUES[:]  # copying
    allowed_ign_vals.append('')  # needed so empty list are valid in config
    parser.add_argument(
        "--ignore",
        nargs="+",
        default=[],
        choices=allowed_ign_vals,
        metavar=ignore_metavar,
        dest="ignore_list",
        help="Ignore a section to not be printed",
    )
    allowed_show_vals = ALLOWED_SHOW_VALUES[:]  # copying
    allowed_show_vals.append('')  # needed so empty list are valid in config
    parser.add_argument(
        "--show",
        nargs="+",
        default=[],
        dest="show_list",
        choices=allowed_show_vals,
        help="Show more details"
    )

    parser.add_argument(
        "--rdns-lookup",
        action="store_true",
        default=False,
        help="Resolve the ip-address of an execution nodes"
             " to their dns entry"
    )

    parser.add_argument(
        "--tolerated-usage",
        type=float,
        help="Threshold to warn the user, "
             "when a given percentage is exceeded "
             "between used and requested resources",
        default=TOLERATED_USAGE
    )

    parser.add_argument(
        "--bad-usage",
        type=float,
        help="Threshold to signal overuse/waste of resources, "
             "when a given percentage is exceeded "
             "between used and requested resources",
        default=BAD_USAGE
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "-c", "--config",
        is_config_file=True,
        help="Path to config file"
    )
    action.add_argument(
        "--ignore-config",
        action="store_true",
        help="Do not search for config"
    )

    return parser

