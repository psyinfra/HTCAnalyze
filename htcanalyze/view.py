"""Display module to create visual output."""

import os
import sys
import logging
from typing import List

from rich import print as rprint
from rich.table import Table, box
from htcanalyze.htcanalyze import HTCAnalyze, CondorLog
from htcanalyze.globals import NORMAL_EXECUTION


def check_for_redirection() -> (bool, bool, list):
    """Check if reading from stdin or redirecting stdout."""
    redirecting_stdout = not sys.stdout.isatty()
    reading_stdin = not sys.stdin.isatty()
    stdin_input = None

    if reading_stdin:
        stdin_input = sys.stdin.readlines()

    return redirecting_stdout, reading_stdin, stdin_input


def read_file(file: str):
    """
    Read a file.

    :param: file
    :return: content
    """
    output_string = ""
    try:

        if os.path.getsize(file) == 0:
            return output_string

        with open(file, "r", encoding='utf-8') as output_content:
            output_string = output_content.read()
    except NameError as err:
        logging.exception(err)
    except FileNotFoundError:
        rprint(f"[yellow]There is no file: {file}")
    except TypeError as err:
        logging.exception(err)

    return output_string


class View:
    pass


class SingleLogfileView(View):

    def __init__(
            self,
            ext_log="",
            ext_out=".out",
            ext_err=".err",
            show_legend=False
    ):
        self.ext_log = ext_log
        self.ext_out = ext_out
        self.ext_err = ext_err

    @staticmethod
    def print_job_details(job_details):

        job_details_table = Table(
            *["Description", "Value"],
            title="Job Details",
            show_header=False,
            header_style="bold magenta",
            box=box.ASCII
        )
        job_details_table.add_row(
            "State",
            job_details.state_manager.state.name
        )
        job_details_table.add_row(
            "Submitter Address",
            job_details.set_events.submitter_address
        )
        job_details_table.add_row(
            "Host Address",
            job_details.set_events.host_address
        )
        job_details_table.add_row(
            "Return Value",
            str(job_details.set_events.return_value)
        )

        rprint(job_details_table)

    @staticmethod
    def print_times(time_manager):
        time_table = Table(
            *["Description", "Timestamp", "Duration"],
            title="Job Dates and Times",
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )
        time_table.add_row(
            "Submission",
            str(time_manager.submission_date),
            str(time_manager.waiting_time)
        )
        time_table.add_row(
            "Execution",
            str(time_manager.submission_date),
            str(time_manager.execution_time),
        )
        time_table.add_row(
            "Termination",
            str(time_manager.submission_date),
            str(time_manager.total_runtime)

        )

        rprint(time_table)

    @staticmethod
    def print_resources(resources):
        if not resources:
            return

        resource_table = Table(
            *["Partitionable Resources", "Usage ", "Request", "Allocated"],
            title="Job Resources",
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )
        for resource in resources.resources:
            resource_table.add_row(
                resource.description,
                str(resource.usage),
                str(resource.requested),
                str(resource.allocated)
            )

        rprint(resource_table)

    @staticmethod
    def print_ram_history(ram_history, show_legend=True):
        print(ram_history.plot_ram(show_legend=show_legend))

    @staticmethod
    def print_error_events(error_events):
        if not error_events.error_events:
            return

        error_table = Table(
            *["Event Number", "Time Stamp", "Error Code", "Reason"],
            title="Error Events",
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )
        for error in error_events.error_events:
            error_table.add_row(
                str(error.event_number),
                error.time_stamp.strftime("%m/%d %H:%M:%S"),
                error.error_code.name,
                error.reason
            )

        rprint(error_table)

    def print_condor_log(
            self,
            condor_log: CondorLog,
            show_out=False,
            show_err=False,
            show_legend=True
    ) -> str:

        rprint(
            f"[blue]Job Analysis of {os.path.basename(condor_log.file)}[/blue]"
        )

        self.print_job_details(condor_log.job_details)

        self.print_times(condor_log.job_details.time_manager)

        self.print_resources(condor_log.job_details.resources)

        self.print_ram_history(
            condor_log.ram_history,
            show_legend=show_legend
        )

        self.print_error_events(condor_log.error_events)

        if show_out:
            print(read_file(condor_log.job_spec_id + self.ext_out))

        if show_err:
            print(read_file(condor_log.job_spec_id + self.ext_err))

        print("+-+"*30)


def print_results(
        htcanalyze: HTCAnalyze,
        log_files: List[str],
        one_by_one: bool,
        ignore_list=list,
        **__
):
    if not log_files:
        print("No files to process")
        sys.exit(NORMAL_EXECUTION)

    if one_by_one or len(log_files) == 1:
        analyzed_logs = htcanalyze.analyze_logs(log_files)
        view = SingleLogfileView()
        for log in analyzed_logs:
            view.print_condor_log(log)

    else:
        results = htcanalyze.summarize(log_files)

    sys.exit(NORMAL_EXECUTION)
