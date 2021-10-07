"""Display module to create visual output."""

import os
import sys
from abc import ABC
import logging
from typing import List

from rich import print as rprint
from rich.table import Table, box
from rich.progress import Progress
from .log_analyzer import HTCAnalyzer, CondorLog
from .log_summarizer import HTCSummarizer
from .globals import NORMAL_EXECUTION, BAD_USAGE, TOLERATED_USAGE


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


class View(ABC):

    def __init__(
            self,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE
    ):
        self.bad_usage = bad_usage
        self.tolerated_usage = tolerated_usage


class SingleLogfileView(View):

    def __init__(
            self,
            bad_usage,
            tolerated_usage,
            ext_out=".out",
            ext_err=".err"
    ):
        super(SingleLogfileView, self).__init__(bad_usage, tolerated_usage)
        self.ext_out = ext_out
        self.ext_err = ext_err

    def print_job_details(self, job_details, print_times=True):
        if job_details.set_events.is_empty():
            return

        job_details_table = Table(
            *["Description", "Value"],
            # title="Job Details",
            show_header=False,
            header_style="bold magenta",
            box=box.ASCII
        )
        job_details_table.add_row(
            "State",
            str(job_details.state_manager)
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

        if print_times:
            self.print_times(job_details.time_manager)

    @staticmethod
    def print_times(time_manager):
        time_table = Table(
            *["Description", "Timestamp", "Duration"],
            # title="Job Dates and Times",
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
            str(time_manager.execution_date),
            str(time_manager.execution_time),
        )
        time_table.add_row(
            "Termination",
            str(time_manager.termination_date),
            str(time_manager.total_runtime)
        )

        rprint(time_table)

    @staticmethod
    def print_resources(
            resources,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE
    ):
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
            resource.chg_lvl_by_threholds(
                bad_usage=bad_usage,
                tolerated_usage=tolerated_usage
            )
            resource_table.add_row(
                resource.description,
                resource.get_usage_colored(),
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
            time_stamp = (
                error.time_stamp.strftime("%m/%d %H:%M:%S")
                if error.time_stamp else None
            )
            error_table.add_row(
                str(error.event_number),
                time_stamp,
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
            f"[blue]Job Analysis of [/blue]"
            f"[cyan]{os.path.basename(condor_log.file)}[/cyan]"
        )

        self.print_job_details(condor_log.job_details)

        self.print_resources(
            condor_log.job_details.resources,
            self.bad_usage,
            self.tolerated_usage
        )

        self.print_ram_history(
            condor_log.ram_history,
            show_legend=show_legend
        )

        self.print_error_events(condor_log.error_events)

        if show_out:
            print(read_file(condor_log.job_spec_id + self.ext_out))

        if show_err:
            print(read_file(condor_log.job_spec_id + self.ext_err))


class SummarizedView(View):
    pass


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
    if not log_files:
        print("No files to process")
        sys.exit(NORMAL_EXECUTION)

    # create progressbar, do not redirect output
    with Progress(
            transient=True,
            redirect_stdout=False,
            redirect_stderr=False
    ) as progress:

        task = progress.add_task("Analysing files...", total=len(log_files))

        htc_analyze = HTCAnalyzer(rdns_lookup=rdns_lookup)
        condor_logs = htc_analyze.analyze(log_files)
        analyzed_logs = []
        for condor_log in condor_logs:
            progress.update(task, advance=1)
            analyzed_logs.append(condor_log)

    if mode == 'analyze' or len(log_files) == 1:
        view = SingleLogfileView(
            bad_usage=bad_usage,
            tolerated_usage=tolerated_usage
        )
        for i, log in enumerate(analyzed_logs):
            view.print_condor_log(
                log,
                show_out=show_out,
                show_err=show_err,
                show_legend=show_legend
            )
            if i < len(analyzed_logs)-1:
                print("~"*80)

    else:
        htc_state_summarize = HTCSummarizer(analyzed_logs)
        summarized_logs = htc_state_summarize.summarize()

    sys.exit(NORMAL_EXECUTION)
