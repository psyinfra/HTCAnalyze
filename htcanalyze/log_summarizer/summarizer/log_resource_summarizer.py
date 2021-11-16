"""Module to summarize log resources"""
from typing import List

from htcanalyze.log_analyzer.condor_log.logresource import LogResources
from .summarizer import Summarizer


class LogResourceSummarizer(Summarizer):
    """
    Summarizes log resources

    :param m_log_resources: multiple log resources
    :param ignore_empty: ignore empty resources for the calculation
    """
    def __init__(
            self,
            m_log_resources: List[LogResources] = None,
            ignore_empty=False
    ):
        self.m_log_resources = m_log_resources if m_log_resources else []
        self.ignore_empty = ignore_empty  # todo

    def summarize(self) -> LogResources:
        """Calculates average of log resources."""
        return sum(self.m_log_resources) / len(self.m_log_resources)
