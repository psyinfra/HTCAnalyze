from abc import ABC, abstractmethod
from typing import List

from . import Summarizer, TimeSummarizer, LogResourceSummarizer, NodeSummarizer
from htcanalyze.log_summarizer import SummarizedCondorLogs
from htcanalyze.log_analyzer import CondorLog


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


class NormalTerminationStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(NormalTerminationStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        resource_summarizer = LogResourceSummarizer(
            [cl.job_details.resources for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_resources = resource_summarizer.summarize()

        time_summarizer = TimeSummarizer(
            [cl.job_details.time_manager for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_times = time_summarizer.summarize()

        node_summarizer = NodeSummarizer(
            [cl.job_details for cl in self.condor_logs]
        )
        nodes = node_summarizer.summarize()

        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times,
            avg_resources,
            nodes
        )


class AbnormalTerminationStateSummarizer(NormalTerminationStateSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbnormalTerminationStateSummarizer, self).__init__(condor_logs)


class WaitingStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(WaitingStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        time_summarizer = TimeSummarizer(
            [cl.job_details.time_manager for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_times = time_summarizer.summarize()

        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times
        )


class RunningStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(RunningStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:

        time_summarizer = TimeSummarizer(
            [cl.job_details.time_manager for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_times = time_summarizer.summarize()

        node_summarizer = NodeSummarizer(
            [cl.job_details for cl in self.condor_logs]
        )
        summarized_node_jobs = node_summarizer.summarize()

        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_node_jobs=summarized_node_jobs
        )


class AbortedStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbortedStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs
        )


class ErrorWhileReadingStateSummarizer(CondorLogSummarizer):
    def __init__(self, condor_logs: List[CondorLog]):
        super(ErrorWhileReadingStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs
        )
