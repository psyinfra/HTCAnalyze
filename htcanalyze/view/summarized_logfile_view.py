"""Module to create a view for summarized log files."""
from datetime import timedelta
from typing import List

from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE
from .view import View
from .resource_view import ResourceView
from ..log_summarizer.summarized_condor_logs.summarized_condor_logs import (
    SummarizedCondorLogs
)


class SummarizedLogfileView(View):
    """Visualizes summarized log files."""

    def print_times(
            self,
            job_times
    ):
        """Prints job times table."""
        if not job_times:
            return
        if job_times.is_empty():
            return

        time_table = self.create_table(
            ["Description", "Duration"],
            # title="Job Dates and Times",
        )
        if not job_times.waiting_time == timedelta():
            time_table.add_row(
                "Average Waiting Time",
                str(job_times.waiting_time)
            )
        if not job_times.execution_time == timedelta():
            time_table.add_row(
                "Average Execution Time",
                str(job_times.execution_time),
            )
        if not job_times.total_runtime == timedelta():
            time_table.add_row(
                "Average Runtime (Total)",
                str(job_times.total_runtime)
            )

        self.console.print(time_table)

    def print_summarized_node_jobs(
            self,
            summarized_node_jobs,
            sort_by_n_jobs: bool = True
    ):
        """
        Prints summarized node jobs table,
        sorted by the number of jobs.

        :param summarized_node_jobs:
        :param sort_by_n_jobs:
        :return:
        """
        if not summarized_node_jobs:
            return

        node_table = self.create_table(
            [
                "Node Address",
                "No. of Jobs",
                "Avg. Waiting Time",
                "Avg. Execution Time",
                "Avg. Runtime (Total)"
            ]
        )

        if sort_by_n_jobs:
            summarized_node_jobs = sorted(summarized_node_jobs, reverse=True)

        for summarized_node in summarized_node_jobs:
            node_table.add_row(
                summarized_node.address,
                str(summarized_node.n_jobs),
                str(summarized_node.job_times.waiting_time),
                str(summarized_node.job_times.execution_time),
                str(summarized_node.job_times.total_runtime)
            )

        self.console.print(node_table)

    def print_summarized_error_events(
            self,
            summarized_error_states,
            sort_by_n_error_events=True,
            file_lim=3
    ):
        """
        Print summarized error events,
        sorted by the number of events.
        Prints file names if less than file_lim files have such an error event,
        else only the number is printed to keep the output readable.

        :param summarized_error_states:
        :param sort_by_n_error_events:
        :param file_lim:
        :return:
        """
        if not summarized_error_states:
            return

        if sort_by_n_error_events:
            summarized_error_states = sorted(
                summarized_error_states, reverse=True
            )

        headers = ["Error Event", "No. of Occurrences"]
        use_file_lim = True
        for ses in summarized_error_states:
            if len(ses.files) > file_lim:
                use_file_lim = False
                break

        if use_file_lim:
            headers.append("Files")

            def file_func(files):
                return "\n".join(files)

        else:
            headers.append("No. of Files")

            def file_func(files):
                return str(len(files))

        error_table = self.create_table(
            headers,
            title="Occurred Job Error Events"
        )
        for summarized_error_state in summarized_error_states:
            error_table.add_row(
                summarized_error_state.error_state.name,
                str(summarized_error_state.n_error_events),
                file_func(summarized_error_state.files)
            )

        self.console.print(error_table)

    def print_summarized_condor_logs(
            self,
            summarized_condor_logs: List[SummarizedCondorLogs],
            sort_states_by_n_jobs=True,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE,
            sep_char='~'
    ):
        """
        Prints summarized log files
        sorts description table by number of files per state,
        separates each state summary by a line of sep_char

        :param summarized_condor_logs:
        :param sort_states_by_n_jobs:
        :param bad_usage:
        :param tolerated_usage
        :param sep_char:
        :return:
        """
        if sort_states_by_n_jobs:
            summarized_condor_logs = sorted(
                summarized_condor_logs, reverse=True
            )

        jobs_table = self.create_table(
            ["State", "No. of Jobs"],
            title="Number of Jobs per State",
        )
        for state_summarized_logs in summarized_condor_logs:
            color = state_summarized_logs.state.color
            jobs_table.add_row(
                f"[{color}]{state_summarized_logs.state.name}[/{color}]",
                str(state_summarized_logs.n_jobs)
            )

        self.console.print(jobs_table)
        self.console.print(sep_char * self.window_width)

        for state_summarized_logs in summarized_condor_logs:

            self.console.print()

            color = state_summarized_logs.state.color
            self.print_desc_line(
                "Log files with JobState:",
                state_summarized_logs.state.name,
                color=color
            )

            self.print_times(state_summarized_logs.avg_times)

            resource_view = ResourceView(
                console=self.console,
                resources=state_summarized_logs.avg_resources,
                bad_usage=bad_usage,
                tolerated_usage=tolerated_usage,
            )
            resource_view.print_resources(
                headers=[
                    "Partitionable Resources",
                    "Avg. Usage",
                    "Avg. Request",
                    "Avg. Allocated"
                ]
            )

            self.print_summarized_node_jobs(
                state_summarized_logs.summarized_node_jobs
            )

            self.print_summarized_error_events(
                state_summarized_logs.summarized_error_states
            )

            self.console.print()
            self.console.print(sep_char * self.window_width)
