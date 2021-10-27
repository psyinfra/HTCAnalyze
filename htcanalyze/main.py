"""
Handle config setup and commandline arguments.

Create visible output by using htcanalyze.
"""

import logging
import argparse
import subprocess

from typing import List
from datetime import datetime as date_time
from configargparse import ArgumentParser, HelpFormatter
from rich.console import Console

# own classes
from .log_analyzer.logvalidator import LogValidator
from .log_analyzer.htcanalyzer import HTCAnalyzer
from .log_summarizer.htcsummarizer import HTCSummarizer
from .view.view import track_progress
from .view.analyzed_logfile_view import AnalyzedLogfileView
from .view.summarized_logfile_view import SummarizedLogfileView
from .globals import *
from . import setup_logging_tool


class HTCAnalyzeException(Exception):

    def __init__(self, *args):
        super().__init__(*args)
        self.message = args[0]


class HTCAnalyzeTerminationEvent(Exception):

    def __init__(self, *args):
        super().__init__(*args)
        self.message = args[0]
        self.exit_code = args[1]


def check_for_redirection() -> (bool, bool, list):
    """Check if reading from stdin or redirecting stdout."""
    redirecting_stdout = not sys.stdout.isatty()
    reading_stdin = not sys.stdin.isatty()
    stdin_input = None

    if reading_stdin:
        stdin_input = sys.stdin.readlines()

    return redirecting_stdout, reading_stdin, stdin_input


def version():
    """Get version from setup.py."""
    output = subprocess.check_output(
        "python -W ignore setup.py --version",
        shell=True
    )
    return output.decode('utf-8').split('\n', maxsplit=1)[0]


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
    return parser


def setup_commandline_parser(
        default_config_files=None
) -> ArgumentParser:
    """
    Define parser with all arguments listed below.

    :param default_config_files: list with config file hierarchy to look for
    :return: parser
    """
    if default_config_files is None:
        default_config_files = []

    parser = ArgumentParser(
        formatter_class=CustomFormatter,
        default_config_files=default_config_files,
        description="Analyze or summarize HTCondor-Joblogs"
    )

    parser.add_argument(
        "path",
        nargs="*",
        action="append",
        default=[],
        help="ANY number of paths to log file(s)"
    )
    # also to add files with different destination,
    # to be used for config file / escaping flags with action=append
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=None,
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
        default=None
    )
    parser.add_argument(
        "--generate-log-file",
        nargs="?",
        const="htcanalyze.log",
        default=None,
        help="generates output about the process, "
             "which is mostly useful for developers, "
             "if no file is specified, "
             "default: htcanalyze.log"
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
        type=str
    )
    parser.add_argument(
        "--ext-out",
        help="Suffix of job out logs (default: .out)",
        type=str
    )
    parser.add_argument(
        "--ext-err",
        help="Suffix of job error logs (default: .err)",
        type=str
    )

    ignore_metavar = (
            "{" + ALLOWED_IGNORE_VALUES[0] + " ... " +
            ALLOWED_IGNORE_VALUES[-1] + "}"
    )
    allowed_ign_vals = ALLOWED_IGNORE_VALUES[:]  # copying
    allowed_ign_vals.append('')  # needed so empty list are valid in config
    parser.add_argument(
        "--ignore",
        nargs="+",
        action="append",
        choices=allowed_ign_vals,
        metavar=ignore_metavar,
        dest="ignore_list",
        default=[],
        help="Ignore a section to not be printed"
    )
    allowed_show_vals = ALLOWED_SHOW_VALUES[:]  # copying
    allowed_show_vals.append('')  # needed so empty list are valid in config
    parser.add_argument(
        "--show",
        nargs="+",
        action="append",
        dest="show_list",
        choices=allowed_show_vals,
        default=[],
        help="Show more details"
    )

    parser.add_argument(
        "--rdns-lookup",
        action="store_true",
        default=None,
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
    parser.add_argument(
        "-c", "--config",
        is_config_file=True,
        help="ONE path to config file"
    )
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Do not search for config"
    )

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
        raise HTCAnalyzeTerminationEvent(
            "Get current version",
            NORMAL_EXECUTION
        )

    # get files from prio_parsed
    files_list = []

    if prio_parsed.config:
        # do not use config files if --no-config flag is set
        if prio_parsed.no_config:
            # if as well config is set, exit, because of conflict
            raise HTCAnalyzeException(
                "conflict between --no-config and --config"
            )
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

        # remove empty string from lists, because configargparse
        # inserts empty strings, when list is empty
        for val in cmd_dict.keys():
            if isinstance(cmd_dict[val], list):
                for item in cmd_dict[val]:
                    if len(item) == 1 and item[0] == "":
                        item.remove("")

    else:
        cmd_parser = setup_commandline_parser()
        commands_parsed = cmd_parser.parse_args(args)
        # extend files list by given paths
        for item in commands_parsed.path:
            files_list.extend(item)
        cmd_dict = vars(commands_parsed).copy()

    del cmd_dict["path"]
    cmd_dict["files"] = files_list

    # concat ignore list
    new_ignore_list = []
    for item in cmd_dict["ignore_list"]:
        new_ignore_list.extend(item)
    cmd_dict["ignore_list"] = new_ignore_list

    # concat show list
    new_show_list = []
    for item in cmd_dict["show_list"]:
        new_show_list.extend(item)
    cmd_dict["show_list"] = new_show_list

    # error handling
    if cmd_dict["show_list"] and not cmd_dict["analyze"]:
        raise HTCAnalyzeException(
            "--show only allowed with analyze mode"
        )

    # delete unnecessary information
    del cmd_dict["version"]
    del cmd_dict["no_config"]

    if cmd_dict['ext_log'] is None:
        cmd_dict['ext_log'] = ""
    elif not cmd_dict['ext_log'].startswith('.'):
        cmd_dict['ext_log'] = f".{cmd_dict['ext_log']}"

    if cmd_dict['analyze'] is True:
        cmd_dict['mode'] = 'analyze'
    else:
        cmd_dict['mode'] = 'summarize'

    if cmd_dict['ext_err'] is None:
        cmd_dict['ext_err'] = ".err"
    elif not cmd_dict['ext_err'].startswith('.'):
        cmd_dict['ext_err'] = f".{cmd_dict['ext_err']}"

    if cmd_dict['ext_out'] is None:
        cmd_dict['ext_out'] = ".out"
    elif not cmd_dict['ext_out'].startswith('.'):
        cmd_dict['ext_out'] = f".{cmd_dict['ext_out']}"

    return cmd_dict


def print_results(
        log_files: List[str],
        mode='summarize',
        rdns_lookup=False,
        bad_usage=BAD_USAGE,
        tolerated_usage=TOLERATED_USAGE,
        show_legend=True,
        show_err=False,
        show_out=False,
        **__
):
    htc_analyze = HTCAnalyzer(rdns_lookup=rdns_lookup)
    condor_logs = htc_analyze.analyze(log_files)

    if mode == 'analyze' or len(log_files) == 1:
        view = AnalyzedLogfileView(
            bad_usage=bad_usage,
            tolerated_usage=tolerated_usage
        )
        analyzed_logs = track_progress(
            condor_logs,
            len(log_files),
            tracking_title="Analyzing files ..."
        )
        view.print_condor_logs(
            analyzed_logs,
            show_legend=show_legend,
            show_err=show_err,
            show_out=show_out
        )

    else:
        view = SummarizedLogfileView()
        analyzed_logs = track_progress(
            condor_logs,
            len(log_files),
            tracking_title="Summarizing files ..."
        )
        htc_state_summarizer = HTCSummarizer(analyzed_logs)
        summarized_condor_logs = htc_state_summarizer.summarize()
        view.print_summarized_condor_logs(summarized_condor_logs)


def run(commandline_args):
    """
    Run this script.

    :param commandline_args: list of args
    :return:
    """
    if not isinstance(commandline_args, list):
        commandline_args = commandline_args.split()

    console = Console()

    try:

        redirecting_stdout, reading_stdin, std_input = check_for_redirection()

        if reading_stdin and std_input is not None:
            for line in std_input:
                commandline_args.extend(line.rstrip('\n').split(" "))

        param_dict = manage_params(commandline_args)

        setup_logging_tool(
            param_dict["generate_log_file"],
            param_dict["verbose"]
        )

        if reading_stdin:
            logging.debug("Reading from stdin")
        if redirecting_stdout:
            logging.debug("Output is getting redirected")

        validator = LogValidator(
            ext_log=param_dict["ext_log"],
            ext_out=param_dict["ext_out"],
            ext_err=param_dict["ext_err"]
        )
        valid_files_generator = validator.common_validation(
            param_dict["files"],
            recursive=param_dict["recursive"]
        )
        with console.status("[bold green]Validating files ..."):
            valid_files = [
                file_path for file_path in valid_files_generator
            ]

        console.print(
            f"[green]{len(valid_files)} valid log file(s)[/green]\n"
        )

        if not valid_files:
            raise HTCAnalyzeTerminationEvent(
                "No valid HTCondor log files found",
                NO_VALID_FILES
            )

        print_results(
            log_files=valid_files,
            show_legend=False,
            **param_dict
        )

    except HTCAnalyzeException as err:
        raise HTCAnalyzeTerminationEvent(err, HTCANALYZE_ERROR)

    except TypeError as err:
        raise HTCAnalyzeTerminationEvent(err, TYPE_ERROR)

    except KeyboardInterrupt:
        raise HTCAnalyzeTerminationEvent(
            "Script was interrupted by the user",
            KEYBOARD_INTERRUPT
        )


def main():
    """main function (entry point)."""
    console = Console()
    try:
        logging.debug("-------Start of htcanalyze script-------")
        start = date_time.now()
        run(sys.argv[1:])
        end = date_time.now()
        logging.debug(f"Runtime: {end - start}")
        logging.debug("-------End of htcanalyze script-------")
        sys.exit(NORMAL_EXECUTION)
    except HTCAnalyzeTerminationEvent as err:
        if not err.exit_code == NORMAL_EXECUTION:
            logging.debug(err.message)
            console.print(f"[red]{err.message}[/red]")
        sys.exit(err.exit_code)


if __name__ == "main":
    main()
