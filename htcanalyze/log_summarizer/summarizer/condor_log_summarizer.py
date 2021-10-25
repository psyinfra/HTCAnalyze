from abc import ABC, abstractmethod
from typing import List

from .summarizer import Summarizer
from .log_resource_summarizer import LogResourceSummarizer
from .time_summarizer import TimeSummarizer
from .node_summarizer import NodeSummarizer
from .error_event_summarizer import ErrorEventSummarizer
from ..summarized_condor_logs.summarized_condor_logs import (
    SummarizedCondorLogs
)
from htcanalyze.log_analyzer.condor_log.condor_log import CondorLog


class CondorLogSummarizer(Summarizer, ABC):

    def __init__(self, condor_logs, state=None):
        self.condor_logs = condor_logs
        self.state = state
        resources, time_managers, nodes, logfiles_error_events = (
            self._get_data()
        )
        self.resource_summarizer = LogResourceSummarizer(
            resources,
            ignore_empty=False  # Todo
        )
        self.time_summarizer = TimeSummarizer(
            time_managers,
            ignore_empty=False  # Todo
        )
        self.node_summarizer = NodeSummarizer(nodes)
        self.error_event_summarizer = ErrorEventSummarizer(
            logfiles_error_events
        )

    def _get_data(self):
        resources = []
        time_managers = []
        nodes = []
        log_files_error_events = []
        for cl in self.condor_logs:
            resources.append(cl.job_details.resources)
            time_managers.append(cl.job_details.time_manager)
            nodes.append(cl.job_details)
            log_files_error_events.append(cl.logfile_error_events)

        return resources, time_managers, nodes, log_files_error_events

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

        avg_resources = self.resource_summarizer.summarize()
        avg_times = self.time_summarizer.summarize()
        summarized_node_jobs = self.node_summarizer.summarize()
        summarized_error_events = self.error_event_summarizer.summarize()

        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times,
            avg_resources,
            summarized_node_jobs,
            summarized_error_events
        )


class AbnormalTerminationStateSummarizer(NormalTerminationStateSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbnormalTerminationStateSummarizer, self).__init__(condor_logs)


class WaitingStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(WaitingStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        avg_times = self.time_summarizer.summarize()
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_error_states=summarized_error_states
        )


class RunningStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(RunningStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:

        avg_times = self.time_summarizer.summarize()
        summarized_node_jobs = self.node_summarizer.summarize()
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_node_jobs=summarized_node_jobs,
            summarized_error_states=summarized_error_states
        )


class AbortedStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbortedStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        avg_times = self.time_summarizer.summarize()
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_error_states=summarized_error_states
        )


class ErrorWhileReadingStateSummarizer(CondorLogSummarizer):
    def __init__(self, condor_logs: List[CondorLog]):
        super(ErrorWhileReadingStateSummarizer, self).__init__(condor_logs)

    def summarize(self) -> SummarizedCondorLogs:
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            summarized_error_states=summarized_error_states
        )
