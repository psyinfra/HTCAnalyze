
from datetime import timedelta
from typing import List

from rich.table import Table, box
from rich.text import Text

from .view import View
from htcanalyze.log_summarizer.summarizer import SummarizedCondorLogs


class SummarizedLogfileView(View):

    def __init__(self):
        super(SummarizedLogfileView, self).__init__()

    def print_times(
            self,
            job_times
    ):
        if not job_times:
            return
        if job_times.is_empty():
            return

        time_table = Table(
            *["Description", "Duration"],
            # title="Job Dates and Times",
            width=self.window_width,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
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
            sort_by_n_jobs=True
    ):
        if not summarized_node_jobs:
            return

        headers = [
            "Node Address",
            "Jobs",
            "Avg. Waiting Time",
            "Avg. Execution Time",
            "Avg. Runtime (Total)"
        ]
        node_table = Table(
            *headers,
            # title="Job Dates and Times",
            width=self.window_width,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )

        if sort_by_n_jobs:
            summarized_node_jobs = reversed(sorted(summarized_node_jobs))

        for summarized_node in summarized_node_jobs:
            node_table.add_row(
                summarized_node.address,
                str(summarized_node.n_jobs),
                str(summarized_node.job_times.waiting_time),
                str(summarized_node.job_times.execution_time),
                str(summarized_node.job_times.total_runtime)
            )

        self.console.print(node_table)

    def print_state(self, state, highlight_char="#"):
        color = state.get_jobstate_color()
        desc_str = f"Log files with JobState:"
        # without_color = f"{desc_str} {state.name}"
        with_color = f"{desc_str} [{color}]{state.name}[/{color}]"
        raw_text = Text.from_markup(with_color)

        fill_up_len = int((self.window_width - len(raw_text)) / 2)
        fill_up_str = highlight_char*fill_up_len
        full_state_str = f"{fill_up_str} {raw_text} {fill_up_str}"
        overhang = len(full_state_str) - self.window_width
        fill_up_str2 = fill_up_str[:-overhang]

        print(highlight_char*self.window_width)
        self.console.print(f"{fill_up_str} {with_color} {fill_up_str2}")
        print(highlight_char*self.window_width)

    def print_summarized_condor_logs(
            self,
            summarized_condor_logs: List[SummarizedCondorLogs],
            sort_states_by_n_jobs=True,
            sep_char='~'
    ):
        if sort_states_by_n_jobs:
            summarized_condor_logs = list(
                reversed(sorted(summarized_condor_logs))
            )

        jobs_table = Table(
            *["State", "Jobs"],
            # title="Job Dates and Times",
            width=self.window_width,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )

        for state_summarized_logs in summarized_condor_logs:
            color = state_summarized_logs.state.get_jobstate_color()
            jobs_table.add_row(
                f"[{color}]{state_summarized_logs.state.name}[/{color}]",
                str(state_summarized_logs.n_jobs)
            )

        self.console.print(jobs_table)
        print(sep_char * self.window_width)

        for state_summarized_logs in summarized_condor_logs:

            self.print_state(state_summarized_logs.state)

            self.print_times(state_summarized_logs.avg_times)

            self.print_resources(
                state_summarized_logs.avg_resources,
                title="Average Job Resources"
            )

            self.print_summarized_node_jobs(
                state_summarized_logs.summarized_node_jobs
            )

            print(sep_char * self.window_width)
