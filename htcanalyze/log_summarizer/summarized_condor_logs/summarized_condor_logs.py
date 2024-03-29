"""Module to represent summarized condor logs."""
from typing import List

from htcanalyze import ReprObject
from htcanalyze.log_analyzer.condor_log.time_manager import JobTimes
from htcanalyze.log_analyzer.condor_log.logresource import LogResources
from htcanalyze.log_analyzer.event_handler.states import JobState
from .summarized_node_jobs import SummarizedNodeJobs
from .summarized_error_events import SummarizedErrorState


class SummarizedCondorLogs(ReprObject):
    """
    Represents summarized HTCondor logs.

    :param state: state of the logs
    :param n_jobs: number of jobs (logs)
    :param avg_times: average job times
    :param avg_resources: average log resources
    :param summarized_node_jobs: summarized node jobs
    :param summarized_error_states: summarized error states
    """
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

    def __lt__(self, other):
        return self.n_jobs < other.n_jobs
