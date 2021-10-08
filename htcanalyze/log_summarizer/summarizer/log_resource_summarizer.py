from typing import List

from htcanalyze.log_analyzer.condor_log import LogResources
from .summarizer import Summarizer


class LogResourceSummarizer(Summarizer):

    def __init__(
            self,
            m_log_resources: List[LogResources] = None,
            ignore_empty=False
    ):
        self.m_log_resources = m_log_resources if m_log_resources else []
        self.ignore_empty = ignore_empty  # todo

    def summarize(self):
        return sum(self.m_log_resources) / len(self.m_log_resources)
