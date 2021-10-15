
from datetime import timedelta
from typing import List

from .view import View
from htcanalyze.log_summarizer import SummarizedCondorLogs


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
            sort_by_n_jobs=True
    ):
        if not summarized_node_jobs:
            return

        node_table = self.create_table(
            [
                "Node Address",
                "No. of Jobs",
                "Avg. Waiting Time",
                "Avg. Execution Time",
                "Avg. Runtime (Total)"
            ],
            # title="Job Dates and Times",
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
            sep_char='~'
    ):
        if sort_states_by_n_jobs:
            summarized_condor_logs = sorted(
                summarized_condor_logs, reverse=True
            )

        jobs_table = self.create_table(
            ["State", "No. of Jobs"],
            title="Number of Jobs per State",
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

            print()

            color = state_summarized_logs.state.get_jobstate_color()
            self.print_desc_line(
                "Log files with JobState:",
                state_summarized_logs.state.name,
                color=color
            )

            self.print_times(state_summarized_logs.avg_times)

            self.print_resources(
                state_summarized_logs.avg_resources,
                title="Average Job Resources"
            )

            self.print_summarized_node_jobs(
                state_summarized_logs.summarized_node_jobs
            )

            self.print_summarized_error_events(
                state_summarized_logs.summarized_error_states
            )

            print()
            print(sep_char * self.window_width)
