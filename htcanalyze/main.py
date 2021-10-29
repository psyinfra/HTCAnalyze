"""
Handle config setup and commandline arguments.

Create visible output by using htcanalyze.
"""

import sys
import logging
import subprocess

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
    CONFIG_PATHS,
    BAD_USAGE,
    TOLERATED_USAGE,
    NORMAL_EXECUTION,
    NO_VALID_FILES,
    HTCANALYZE_ERROR,
    TYPE_ERROR,
    KEYBOARD_INTERRUPT
)


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


def print_results(
        log_files: List[str],
        analyze=False,
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

    if analyze or len(log_files) == 1:
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
    # else summarize
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

        parser = setup_parser()
        params = parser.get_params(commandline_args)
        setup_logging_tool(params.verbose)

        if params.version:
            print(f"Version: {version()}")
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
            recursive=params.recursive
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
            **vars(params)
        )

    except HTCAnalyzeException as err:
        raise HTCAnalyzeTerminationEvent(err, HTCANALYZE_ERROR)

    except TypeError as err:
        import traceback
        print(traceback.print_exc())
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
