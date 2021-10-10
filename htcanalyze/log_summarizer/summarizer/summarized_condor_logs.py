from typing import List

from htcanalyze.log_analyzer.condor_log import CondorLog, \
    JobTimes, LogResources
from .node_summarizer import SummarizedNodeJobs


class SummarizedCondorLogs:

    def __init__(
            self,
            avg_times: JobTimes = None,
            avg_resources: LogResources = None,
            summarized_node_jobs: List[SummarizedNodeJobs] = None
    ):
        self.avg_times = avg_times
        self.avg_resources = avg_resources
        self.summarized_node_jobs = summarized_node_jobs