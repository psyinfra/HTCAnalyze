from abc import ABC, abstractmethod

from .summarizer import Summarizer
from .summarized_condor_logs import SummarizedCondorLogs


class CondorLogSummarizer(Summarizer, ABC):

    def __init__(self, condor_logs, state=None):
        self.condor_logs = condor_logs
        self.state = state

    @abstractmethod
    def summarize(self) -> SummarizedCondorLogs:
        pass

    @property
    def n_jobs(self):
        return len(self.condor_logs)



