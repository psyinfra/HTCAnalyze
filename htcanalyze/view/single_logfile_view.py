import os

from rich.table import Table, box
from rich import print as rprint

from htcanalyze.log_analyzer import CondorLog
from .view import View, read_file


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
