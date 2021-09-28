"""
Handle config setup and commandline arguments.

Create visible output by using htcanalyze.

Exit Codes:
    Normal Termination: 0
    No given files: 1
    Wrong Options or Arguments: 2
    TypeError: 3
    Keyboard interruption: 4
"""

import argparse
import logging
import sys
import subprocess
from datetime import datetime as date_time

import configargparse
from argparse import HelpFormatter
from rich import print as rprint

# own classes
from htcanalyze.display import print_results, check_for_redirection
from htcanalyze import setup_logging_tool
from htcanalyze.htcanalyze import HTCAnalyze, raise_value_error
from htcanalyze.logvalidator import LogValidator
from htcanalyze.globals import *


def version():
    output = subprocess.check_output(
        "python -W ignore setup.py --version",
        shell=True
    )
    return output.decode('utf-8').split('\n')[0]


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
                parts.append('%s %s' % (option_string, args_string))
        if sum(len(s) for s in parts) < self._width - (len(parts) - 1) * 2:
            return ', '.join(parts)
        else:
            return ',\n  '.join(parts)


def setup_prioritized_parser():
    """
    Prioritized options.

    :return: parser
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-config",
                        action="store_true")
    parser.add_argument("-c", "--config", nargs=1)
    parser.add_argument("--version",
                        help="Print out version",
                        action="store_true")

    parser.add_argument("-f", "--files",
                        nargs=1,
                        action="append",
                        dest="more_files",
                        default=[],
                        help="ONE path to log file")
    return parser


def setup_commandline_parser(
        default_config_files=[]
) -> configargparse.ArgumentParser:
    """
    Define parser with all arguments listed below.

    :param default_config_files: list with config file hierarchy to look for
    :return: parser
    """
    parser = configargparse.ArgumentParser(
        formatter_class=CustomFormatter,
        default_config_files=default_config_files,
        description="Analyze or summarize HTCondor-Joblogs"
    )

    parser.add_argument("path",
                        nargs="*",
                        action="append",
                        default=[],
                        help="ANY number of paths to log file(s)")
    # also to add files with different destination,
    # to be used for config file / escaping flags with action=append
    parser.add_argument("-f", "--files",
                        nargs=1,
                        action="append",
                        dest="more_files",
                        default=[],
                        help="ONE path to log file")
    parser.add_argument("-r", "--recursive",
                        action="store_true",
                        default=None,
                        help="Recursive search through directory hierarchy")

    parser.add_argument("--version",
                        help="Print out extended execution details",
                        action="store_true")

    parser.add_argument("-v", "--verbose",
                        help="Print out extended execution details",
                        action="store_true",
                        default=None)
    parser.add_argument("--generate-log-file",
                        nargs="?",
                        const="htcanalyze.log",
                        default=None,
                        help="generates output about the process,"
                             " which is mostly useful for developers, "
                             "if no file is specified,"
                             " default: htcanalyze.log")

    parser.add_argument("--one-by-one",
                        action="store_true",
                        default=None,
                        help="Analyze given files one by one")

    parser.add_argument("--ext-log",
                        help="Suffix of HTCondor job logs (default: none)",
                        type=str)
    parser.add_argument("--ext-out",
                        help="Suffix of job out logs (default: .out)",
                        type=str)
    parser.add_argument("--ext-err",
                        help="Suffix of job error logs (default: .err)",
                        type=str)

    ignore_metavar = "{" + ALLOWED_IGNORE_VALUES[0] + " ... " \
                     + ALLOWED_IGNORE_VALUES[-1] + "}"
    allowed_ign_vals = ALLOWED_IGNORE_VALUES[:]  # copying
    allowed_ign_vals.append('')  # needed so empty list are valid in config
    parser.add_argument("--ignore",
                        nargs="+",
                        action="append",
                        choices=allowed_ign_vals,
                        metavar=ignore_metavar,
                        dest="ignore_list",
                        default=[],
                        help="Ignore a section to not be printed")
    allowed_show_vals = ALLOWED_SHOW_VALUES[:]  # copying
    allowed_show_vals.append('')  # needed so empty list are valid in config
    parser.add_argument("--show",
                        nargs="+",
                        action="append",
                        dest="show_list",
                        choices=allowed_show_vals,
                        default=[],
                        help="Show more details")

    parser.add_argument("--rdns-lookup",
                        action="store_true",
                        default=None,
                        help="Resolve the ip-address of an execution nodes"
                             " to their dns entry")

    parser.add_argument("--tolerated-usage",
                        type=float,
                        help="Threshold to warn the user, "
                             "when a given percentage is exceeded "
                             "between used and requested resources")

    parser.add_argument("--bad-usage",
                        type=float,
                        help="Threshold to signal overuse/waste of resources, "
                             "when a given percentage is exceeded "
                             "between used and requested resources")
    parser.add_argument("-c", "--config",
                        is_config_file=True,
                        help="ONE path to config file")
    parser.add_argument("--no-config",
                        action="store_true",
                        help="Do not search for config")

    return parser


def manage_params(args: list) -> dict:
    """
    manage params.

    returns a dict looking like (default):

     {'verbose': False,
      'generate_log_file': None,
      'ext_log': '',
      'ext_out': '.out',
      'ext_err': '.err',
      'ignore_list': [],
      'show_list': [],
      'no_config': False,
      'rdns_lookup': False
      'files': []
      ....
      }

    :param args: list of args
    :return: dict with params
    """
    prio_parsed, args = setup_prioritized_parser().parse_known_args(args)
    # first of all check for prioritised/exit params
    if prio_parsed.version:
        print(f"Version: {version()}")
        sys.exit(NORMAL_EXECUTION)

    # get files from prio_parsed
    files_list = list()
    for log_file in prio_parsed.more_files:
        files_list.extend(log_file)

    if prio_parsed.config:
        # do not use config files if --no-config flag is set
        if prio_parsed.no_config:
            # if as well config is set, exit, because of conflict
            print(
                "htcanalyze: error: conflict between --no-config and --config"
            )
            sys.exit(HTCANALYZE_ERROR)
        # else add config again
        args.extend(["--config", prio_parsed.config[0]])

    # parse config file if not --no-config is set, might change nothing
    if not prio_parsed.no_config:
        cmd_parser = setup_commandline_parser(CONFIG_PATHS)
        commands_parsed = cmd_parser.parse_args(args)
        cmd_dict = vars(commands_parsed).copy()

        # extend files list by given paths
        for log_paths in commands_parsed.path:
            files_list.extend(log_paths)
        # add files, if none are given by terminal
        if not files_list:
            for log_paths in cmd_dict["more_files"]:
                # make sure that empty strings are not getting inserted
                if len(log_paths) == 1 and log_paths[0] != "":
                    files_list.extend(log_paths)

        # remove empty string from lists, because configargparse
        # inserts empty strings, when list is empty
        for val in cmd_dict.keys():
            if isinstance(cmd_dict[val], list):
                for li in cmd_dict[val]:
                    if len(li) == 1 and li[0] == "":
                        li.remove("")

    else:
        cmd_parser = setup_commandline_parser()
        commands_parsed = cmd_parser.parse_args(args)
        # extend files list by given paths
        for li in commands_parsed.path:
            files_list.extend(li)
        cmd_dict = vars(commands_parsed).copy()

    del cmd_dict["path"]
    del cmd_dict["more_files"]
    cmd_dict["files"] = files_list

    # concat ignore list
    new_ignore_list = list()
    for li in cmd_dict["ignore_list"]:
        new_ignore_list.extend(li)
    cmd_dict["ignore_list"] = new_ignore_list

    # concat show list
    new_show_list = list()
    for li in cmd_dict["show_list"]:
        new_show_list.extend(li)
    cmd_dict["show_list"] = new_show_list

    # error handling
    try:
        if cmd_dict["show_list"] and not cmd_dict["one_by_one"]:
            raise_value_error("--show only allowed with analyze mode")
    except ValueError as err:
        rprint(f"[red]htcanalyze: error: {err}[/red]")
        sys.exit(HTCANALYZE_ERROR)

    # delete unnecessary information
    del cmd_dict["version"]
    del cmd_dict["no_config"]

    if cmd_dict['ext_log'] is None:
        cmd_dict['ext_log'] = ""
    elif not cmd_dict['ext_log'].startswith('.'):
        cmd_dict['ext_log'] = f".{cmd_dict['ext_log']}"

    if cmd_dict['ext_err'] is None:
        cmd_dict['ext_err'] = ".err"
    elif not cmd_dict['ext_err'].startswith('.'):
        cmd_dict['ext_err'] = f".{cmd_dict['ext_err']}"

    if cmd_dict['ext_out'] is None:
        cmd_dict['ext_out'] = ".out"
    elif not cmd_dict['ext_out'].startswith('.'):
        cmd_dict['ext_out'] = f".{cmd_dict['ext_out']}"

    return cmd_dict


def run(commandline_args):
    """
    Run this script.

    :param commandline_args: list of args
    :return:
    """
    if not isinstance(commandline_args, list):
        commandline_args = commandline_args.split()

    try:
        start = date_time.now()

        redirecting_stdout, reading_stdin, std_input = check_for_redirection()

        if reading_stdin and std_input is not None:
            for line in std_input:
                commandline_args.extend(line.rstrip('\n').split(" "))

        param_dict = manage_params(commandline_args)

        setup_logging_tool(param_dict["generate_log_file"],
                           param_dict["verbose"])

        logging.debug("-------Start of htcanalyze script-------")

        # do not show legend, if output is redirected
        show_legend = not redirecting_stdout
        htcanalyze = HTCAnalyze(
            ext_log=param_dict["ext_log"],
            ext_out=param_dict["ext_out"],
            ext_err=param_dict["ext_err"],
            show_list=param_dict["show_list"],
            rdns_lookup=param_dict["rdns_lookup"],
            tolerated_usage=param_dict["tolerated_usage"],
            bad_usage=param_dict["bad_usage"],
            show_legend=show_legend
        )

        if param_dict["verbose"]:
            logging.info('Verbose mode turned on')

        if reading_stdin:
            logging.debug("Reading from stdin")
        if redirecting_stdout:
            logging.debug("Output is getting redirected")

        validator = LogValidator(ext_log=param_dict["ext_log"],
                                 ext_out=param_dict["ext_out"],
                                 ext_err=param_dict["ext_err"],
                                 recursive=param_dict["recursive"])

        valid_files = validator.common_validation(param_dict["files"])

        rprint(
            f"[green]{len(valid_files)} valid log file(s)[/green]\n"
        )

        if not valid_files:
            rprint("[red]No valid HTCondor log files found[/red]")
            logging.debug("-------End of htcanalyze script-------")
            sys.exit(NO_VALID_FILES)

        print_results(htcanalyze, log_files=valid_files, **param_dict)

        end = date_time.now()

        logging.debug(f"Runtime: {end - start}")  # runtime of this script

        logging.debug("-------End of htcanalyze script-------")

        sys.exit(NORMAL_EXECUTION)

    except TypeError as err:
        logging.exception(err)
        rprint(f"[red]{err.__class__.__name__}: {err}[/red]")
        sys.exit(TYPE_ERROR)

    except KeyboardInterrupt:
        logging.info("Script was interrupted by the user")
        print("Interrupted by user")
        sys.exit(KEYBOARD_INTERRUPT)


def main():
    """main function (entry point)."""
    run(sys.argv[1:])


if __name__ == "main":
    """execute module."""
    main()
