
from typing import List
from htcanalyze.log_analyzer.condor_log import TimeManager
from .summarizer import Summarizer


class TimeSummarizer(Summarizer):

    def __init__(self, time_managers: List[TimeManager], ignore_empty=False):
        self.job_times = [tm.job_times for tm in time_managers]
        self.ignore_empty = ignore_empty  # Todo

    def summarize(self):
        return sum(self.job_times) / len(self.job_times)