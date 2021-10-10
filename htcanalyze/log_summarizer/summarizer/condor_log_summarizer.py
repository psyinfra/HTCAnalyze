from abc import ABC, abstractmethod

from .summarizer import Summarizer
from .summarized_condor_logs import SummarizedCondorLogs


class CondorLogSummarizer(Summarizer, ABC):

    def __init__(self, condor_logs):
        self.condor_logs = condor_logs

    @abstractmethod
    def summarize(self) -> SummarizedCondorLogs:
        pass
