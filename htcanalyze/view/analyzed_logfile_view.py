"""Module to visualize condor logs."""
import os
from typing import List

from htcanalyze.log_analyzer.condor_log.condor_log import CondorLog
from htcanalyze.globals import STRF_FORMAT
from .view import View


class AnalyzedLogfileView(View):
    """
    View to visualize a single (analyzed) CondorLog

    :param bad_usage: bad usage threshold
    :param tolerated_usage: tolerated usage threshold
    :param ext_out: extension of stdout files
    :param ext_err: extension of stderr files
    """
    def __init__(
            self,
            bad_usage,
            tolerated_usage,
            ext_out=".out",
            ext_err=".err"
    ):
        super().__init__(bad_usage, tolerated_usage)
        self.ext_out = ext_out
        self.ext_err = ext_err

    def print_job_details(self, job_details, print_times=True):
        """Prints job details."""
        if job_details.set_events.is_empty():
            return

        job_details_table = self.create_table(
            ["Description", "Value"],
            # title="Job Details"
        )

        color = job_details.state.color
        job_details_table.add_row(
            "State",
            f"[{color}]{job_details.state.name}[/{color}]"
        )

        job_details_table.add_row(
            "Submitter Address",
            str(job_details.set_events.submitter_address)
        )

        job_details_table.add_row(
            "Host Address",
            str(job_details.set_events.host_address)
        )

        job_details_table.add_row(
            "Return Value",
            str(job_details.set_events.return_value)
        )

        self.console.print(job_details_table)

        if print_times:
            self.print_times(job_details.time_manager)

    def print_times(self, time_manager):
        """Prints time manager data."""
        time_table = self.create_table(
            ["Description", "Timestamp", "Duration"],
            # title="Job Dates and Times"
        )
        if time_manager.rolled_over_year_boundary:
            sub_str = str(time_manager.submission_date)
            exec_str = str(time_manager.execution_date)
            term_str = str(time_manager.termination_date)
        else:
            sub_str = (
                time_manager.submission_date.strftime(STRF_FORMAT) if
                time_manager.submission_date else str(None)
            )
            exec_str = (
                time_manager.execution_date.strftime(STRF_FORMAT) if
                time_manager.execution_date else str(None)
            )
            term_str = (
                time_manager.termination_date.strftime(STRF_FORMAT) if
                time_manager.termination_date else str(None)
            )

        time_table.add_row(
            "Submission",
            sub_str,
            str(time_manager.waiting_time)
        )
        time_table.add_row(
            "Execution",
            exec_str,
            str(time_manager.execution_time),
        )
        time_table.add_row(
            "Termination",
            term_str,
            str(time_manager.total_runtime)
        )

        self.console.print(time_table)

    def print_ram_history(self, ram_history, show_legend=True):
        """Prints ram histogram."""
        if not ram_history.image_size_events:
            return
        self.console.print("Ram Histogram", justify="center")
        print(ram_history.plot_ram(show_legend=show_legend))

    def print_error_events(self, logfile_error_events):
        """Prints error events."""
        if not logfile_error_events.error_events:
            return

        error_table = self.create_table(
            ["Event Number", "Time Stamp", "Error Code", "Reason"],
            title="Error Events"
        )

        for error in logfile_error_events.error_events:
            time_stamp = (
                error.time_stamp.strftime("%m/%d %H:%M:%S")
                if error.time_stamp else None
            )
            error_table.add_row(
                str(error.event_number),
                time_stamp,
                error.error_state.name,
                error.reason
            )

        self.console.print(error_table)

    def print_condor_log(
            self,
            condor_log: CondorLog,
            show_out=False,
            show_err=False,
            show_legend=True
    ):
        """Prints a single condor log."""
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

        self.print_error_events(condor_log.logfile_error_events)

        if show_out:
            print()
            out_file_name = condor_log.job_spec_id + self.ext_out
            self.print_desc_line(
                "Additional stdout output:",
                out_file_name,
                color="blue"
            )
            print(self.read_file(
                os.path.join(os.path.dirname(condor_log.file), out_file_name)
            ))

        if show_err:
            print()
            err_file_name = condor_log.job_spec_id + self.ext_err
            self.print_desc_line(
                "Additional stderr output: ",
                err_file_name,
                color="red"
            )
            print(self.read_file(
                os.path.join(os.path.dirname(condor_log.file), err_file_name)
            ))

    def print_condor_logs(
            self,
            condor_logs: List[CondorLog],
            show_out=False,
            show_err=False,
            show_legend=True,
            sep_char="~"
    ):
        """Prints multiple condor logs."""
        for i, log in enumerate(condor_logs):
            self.print_condor_log(
                log,
                show_out=show_out,
                show_err=show_err,
                show_legend=show_legend
            )
            if i < len(condor_logs)-1:
                print(sep_char*self.window_width)
