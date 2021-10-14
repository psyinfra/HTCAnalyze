import os

from typing import List

from htcanalyze.log_analyzer import CondorLog
from .view import View


class AnalyzedLogfileView(View):

    def __init__(
            self,
            bad_usage,
            tolerated_usage,
            ext_out=".out",
            ext_err=".err"
    ):
        super(AnalyzedLogfileView, self).__init__(bad_usage, tolerated_usage)
        self.ext_out = ext_out
        self.ext_err = ext_err

    def print_job_details(self, job_details, print_times=True):
        if job_details.set_events.is_empty():
            return

        job_details_table = self.create_table(
            ["Description", "Value"],
            # title="Job Details"
        )

        color = job_details.state.get_jobstate_color()
        job_details_table.add_row(
            "State",
            f"[{color}]{job_details.state.name}[/{color}]"
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

        self.console.print(job_details_table)

        if print_times:
            self.print_times(job_details.time_manager)

    def print_times(self, time_manager):
        time_table = self.create_table(
            ["Description", "Timestamp", "Duration"],
            # title="Job Dates and Times"
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

        self.console.print(time_table)

    @staticmethod
    def print_ram_history(ram_history, show_legend=True):
        print(ram_history.plot_ram(show_legend=show_legend))

    def print_error_events(self, error_events):
        if not error_events.error_events:
            return

        error_table = self.create_table(
            ["Event Number", "Time Stamp", "Error Code", "Reason"],
            title="Error Events"
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

        self.console.print(error_table)

    def print_condor_log(
            self,
            condor_log: CondorLog,
            show_out=False,
            show_err=False,
            show_legend=True
    ) -> str:

        self.print_desc_line(
            "Job Analysis of:",
            os.path.basename(condor_log.file),
            color="cyan"
        )

        self.print_job_details(condor_log.job_details)

        self.print_resources(condor_log.job_details.resources)

        self.print_ram_history(
            condor_log.ram_history,
            show_legend=show_legend
        )

        self.print_error_events(condor_log.error_events)

        if show_out:
            print(self.read_file(condor_log.job_spec_id + self.ext_out))

        if show_err:
            print(self.read_file(condor_log.job_spec_id + self.ext_err))

    def print_condor_logs(
            self,
            condor_logs: List[CondorLog],
            show_out=False,
            show_err=False,
            show_legend=True,
            sep_char="~"
    ):
        for i, log in enumerate(condor_logs):
            self.print_condor_log(
                log,
                show_out=show_out,
                show_err=show_err,
                show_legend=show_legend
            )
            if i < len(condor_logs)-1:
                print(sep_char*self.window_width)
