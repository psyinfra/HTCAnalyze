from abc import ABC, abstractmethod

from .summarizer import Summarizer


class CondorLogSummarizer(Summarizer, ABC):

    def __init__(self, condor_logs):
        self.condor_logs = condor_logs

    @abstractmethod
    def summarize(self):
        pass
