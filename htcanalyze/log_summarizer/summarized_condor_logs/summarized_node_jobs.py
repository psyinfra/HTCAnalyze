"""Module to represent summarized node jobs."""
from htcanalyze import ReprObject
from htcanalyze.log_analyzer.condor_log.time_manager import JobTimes


class SingleNodeJob(ReprObject):
    """Single Node saving runtime on a node."""

    def __init__(
            self,
            address: str = None,
            job_times: JobTimes = None
    ):
        self.address = address
        self.job_times = job_times


class SummarizedNodeJobs(SingleNodeJob):
    """
    Create a summarized job representation of jobs executed on a single node.

    :param address: Address of the node
    :param job_times: average job times
    :param n_jobs: Number of jobs executed on the node
    """
    def __init__(
            self,
            address: str = None,
            job_times: JobTimes = None,
            n_jobs: int = None
    ):
        super().__init__(address, job_times)
        self.n_jobs = n_jobs

    def __lt__(self, other):
        return self.n_jobs < other.n_jobs
