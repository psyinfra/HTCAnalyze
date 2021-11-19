"""
Handle config setup and commandline arguments.

Create visible output by using htcanalyze.
"""

import sys
import logging
import subprocess
import traceback

from typing import List
from datetime import datetime as date_time
from rich.console import Console

# own classes
from . import setup_logging_tool
from .log_analyzer.logvalidator import LogValidator
from .log_analyzer.htcanalyzer import HTCAnalyzer
from .log_summarizer.htcsummarizer import HTCSummarizer
from .view.view import track_progress
from .view.analyzed_logfile_view import AnalyzedLogfileView
from .view.summarized_logfile_view import SummarizedLogfileView
from .cli_argument_parser import setup_parser

from .globals import (
    BAD_USAGE,
    TOLERATED_USAGE,
    EXT_ERR_DEFAULT,
    EXT_OUT_DEFAULT,
    NORMAL_EXECUTION,
    NO_VALID_FILES,
    TYPE_ERROR,
    KEYBOARD_INTERRUPT
)


class HTCAnalyzeTerminationEvent(Exception):
    """
    Exception called with a message and an exit code

    :param args: args
        excepts args[0] to be a message an args[1] to be the exit code
    """

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
        "pip show htcanalyze | grep Version",
        shell=True
    )
    return output.decode('utf-8').split()[-1]


def print_results(
        log_files: List[str],
        analyze: bool = False,
        rdns_lookup: bool = False,
        show_legend: bool = True,
        show_list: List = None,
        ext_out: str = EXT_OUT_DEFAULT,
        ext_err: str = EXT_ERR_DEFAULT,
        bad_usage: float = BAD_USAGE,
        tolerated_usage: float = TOLERATED_USAGE,
        console=None,
        **__
) -> None:
    """
    Print results by analyzing the files and using a particular view.

    :param log_files: List[str]
        valid log file paths
    :param analyze: bool, default: False
        whether to analyze the files
    :param rdns_lookup: bool
        reverse dns lookup of ip-addresses
    :param show_legend: bool
        Show legend of RAM histogram if analyzed and possible
    :param show_list: list
        Show more output like stdout or stderr if analyzed
    :param bad_usage: float
        Threshold to signalize a critical percentage
        the usage is away from the requested resources (usually red colored)
    :param ext_out: str
        stdout file extension (default: .out)
    :param ext_err: str
        stderr file extension (default: .err)
    :param tolerated_usage: float
        Threshold to signalize a tolerated but unpleasant percentage
        the usage is away from the requested resources (usually yellow colored)
    :param console: Console
    :param __: ignore unknown params

    :return: None
    """
    if console is None:
        console = Console()
    if show_list is None:
        show_list = []
    # analyze files if only one file was given
    if len(log_files) == 1:
        analyze = True

    htc_analyze = HTCAnalyzer(
        console=console,
        rdns_lookup=rdns_lookup
    )
    condor_logs = htc_analyze.analyze(log_files)

    if analyze:
        view = AnalyzedLogfileView(
            console=console,
            ext_out=ext_out,
            ext_err=ext_err
        )
        analyzed_logs = track_progress(
            condor_logs,
            len(log_files),
            tracking_title="Analyzing files ..."
        )
        view.print_condor_logs(
            analyzed_logs,
            bad_usage=bad_usage,
            tolerated_usage=tolerated_usage,
            show_err="htc-err" in show_list,
            show_out="htc-out" in show_list,
            show_legend=show_legend
        )
    # else summarize
    else:
        view = SummarizedLogfileView(console=console)
        analyzed_logs = track_progress(
            condor_logs,
            len(log_files),
            tracking_title="Summarizing files ..."
        )
        htc_state_summarizer = HTCSummarizer(analyzed_logs)
        summarized_condor_logs = htc_state_summarizer.summarize()
        view.print_summarized_condor_logs(
            summarized_condor_logs,
            bad_usage=bad_usage,
            tolerated_usage=tolerated_usage,
        )


def run(commandline_args, console=None) -> None:
    """
    Run this script.

    :param commandline_args: list of args
    :param console: Console
    :return: None
    """
    if console is None:
        console = Console()
    if not isinstance(commandline_args, list):
        commandline_args = commandline_args.split()

    try:

        redirecting_stdout, reading_stdin, std_input = check_for_redirection()

        if reading_stdin and std_input is not None:
            for line in std_input:
                commandline_args.extend(line.rstrip('\n').split(" "))

        parser = setup_parser()
        params = parser.get_params(commandline_args)
        setup_logging_tool(params.verbose)

        if params.version:
            console.print(f"Version: {version()}")
            raise HTCAnalyzeTerminationEvent(
                "Get current version",
                NORMAL_EXECUTION
            )

        if reading_stdin:
            logging.debug("Reading from stdin")
        if redirecting_stdout:
            logging.debug("Output is getting redirected")

        validator = LogValidator(
            ext_log=params.ext_log,
            ext_out=params.ext_out,
            ext_err=params.ext_err
        )
        valid_files_generator = validator.common_validation(
            params.paths,
            console=console,
            recursive=params.recursive
        )
        with console.status("[bold green]Validating files ..."):
            valid_files = list(valid_files_generator)

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
            console=console,
            **vars(params)
        )

    except TypeError as err:
        console.print(traceback.print_exc())
        raise HTCAnalyzeTerminationEvent(err, TYPE_ERROR) from TypeError

    except KeyboardInterrupt:
        raise HTCAnalyzeTerminationEvent(
            "Script was interrupted by the user",
            KEYBOARD_INTERRUPT
        ) from KeyboardInterrupt


def main():
    """Main function (entry point)."""
    console = Console()
    start = date_time.now()
    exit_code = NORMAL_EXECUTION
    try:
        run(sys.argv[1:], console=console)
    except HTCAnalyzeTerminationEvent as err:
        if not err.exit_code == NORMAL_EXECUTION:
            logging.debug(err.message)
            console.print(f"[red]{err.message}[/red]")
        exit_code = err.exit_code

    end = date_time.now()
    logging.debug("Runtime: %s", end - start)
    logging.debug("-------Script terminated, exit code: %s-------", exit_code)
    sys.exit(exit_code)


if __name__ == "main":
    main()
