
from typing import List

from rich.table import Table, box
from rich import print as rprint

from .view import View
from htcanalyze.log_summarizer.summarizer import SummarizedCondorLogs


class SummarizedLogfileView(View):

    def __init__(self):
        super(SummarizedLogfileView, self).__init__()

    @staticmethod
    def print_times(
            job_times
    ):
        time_table = Table(
            *["Description", "Duration"],
            # title="Job Dates and Times",
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )
        time_table.add_row(
            "Average Waiting Time",
            str(job_times.waiting_time)
        )
        time_table.add_row(
            "Average Execution Time",
            str(job_times.execution_time),
        )
        time_table.add_row(
            "Average Runtime (Total)",
            str(job_times.total_runtime)
        )

        rprint(time_table)

    @staticmethod
    def print_summarized_node_jobs(
            summarized_node_jobs,
            sort_by_n_jobs=True
    ):
        headers = [
            "Node Address",
            "Number of Jobs",
            "Avg. Waiting Time",
            "Avg. Execution Time",
            "Avg. Runtime (Total)"
        ]
        node_table = Table(
            *headers,
            # title="Job Dates and Times",
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

        rprint(node_table)

    def print_summarized_condor_logs(
            self,
            summarized_condor_logs: List[SummarizedCondorLogs]
    ):
        jobs_table = Table(
            *["State", "Number of Jobs"],
            # title="Job Dates and Times",
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

        rprint(jobs_table)
        print("~"*80)

        for state_summarized_logs in summarized_condor_logs:
            color = state_summarized_logs.state.get_jobstate_color()
            rprint(
                f"Log files with JobState: "
                f"[{color}]{state_summarized_logs.state.name}[/{color}]"
            )

            self.print_resources(
                state_summarized_logs.avg_resources,
                title="Average Job Resources"
            )

            self.print_times(
                state_summarized_logs.avg_times
            )

            self.print_summarized_node_jobs(
                state_summarized_logs.summarized_node_jobs
            )

            print("~"*80)
