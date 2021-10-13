import json
from typing import List

from htcanalyze.log_analyzer.condor_log import JobTimes, LogResources
from htcanalyze.log_analyzer.event_handler import JobState
from .summarized_node_jobs import SummarizedNodeJobs


class SummarizedCondorLogs:

    def __init__(
            self,
            state: JobState = None,
            n_jobs: int = None,
            avg_times: JobTimes = None,
            avg_resources: LogResources = None,
            summarized_node_jobs: List[SummarizedNodeJobs] = None
    ):
        self.state = state
        self.n_jobs = n_jobs
        self.avg_times = avg_times
        self.avg_resources = avg_resources
        self.summarized_node_jobs = summarized_node_jobs

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )

    def __lt__(self, other):
        return self.n_jobs < other.n_jobs
