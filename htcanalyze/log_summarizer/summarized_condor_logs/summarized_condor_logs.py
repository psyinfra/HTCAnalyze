import json
from typing import List

from .summarized_node_jobs import SummarizedNodeJobs
from .summarized_error_events import SummarizedErrorState
from htcanalyze.log_analyzer.condor_log.time_manager import JobTimes
from htcanalyze.log_analyzer.condor_log.logresource import LogResources
from htcanalyze.log_analyzer.event_handler.states import JobState


class SummarizedCondorLogs:

    def __init__(
            self,
            state: JobState = None,
            n_jobs: int = None,
            avg_times: JobTimes = None,
            avg_resources: LogResources = None,
            summarized_node_jobs: List[SummarizedNodeJobs] = None,
            summarized_error_states: List[SummarizedErrorState] = None
    ):
        self.state = state
        self.n_jobs = n_jobs
        self.avg_times = avg_times
        self.avg_resources = avg_resources
        self.summarized_node_jobs = summarized_node_jobs
        self.summarized_error_states = summarized_error_states

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )

    def __lt__(self, other):
        return self.n_jobs < other.n_jobs
