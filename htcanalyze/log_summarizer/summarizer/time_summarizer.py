"""Module to summarize time differences."""
from typing import List
from htcanalyze.log_analyzer.condor_log.time_manager import (
    TimeManager,
    JobTimes
)
from .summarizer import Summarizer


class TimeSummarizer(Summarizer):
    """
    Use this class to summarize job times given by a list of time managers

    :param time_managers: List[TimeManger]
        used to summarized job times of each time manager
    :param ignore_empty:
        ignore empty job times
    """
    def __init__(self, time_managers: List[TimeManager], ignore_empty=False):
        self.job_times = [tm.job_times for tm in time_managers]
        self.ignore_empty = ignore_empty  # Todo

    def summarize(self) -> JobTimes:
        """Returns average of job times."""
        return sum(self.job_times) / len(self.job_times)
