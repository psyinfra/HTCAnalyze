"""Module to summarize HTCondor logs."""
from abc import ABC, abstractmethod
from typing import List

from htcanalyze.log_analyzer.condor_log.condor_log import CondorLog, JobDetails
from htcanalyze.log_analyzer.event_handler.states import (
    WaitingState,
    RunningState,
    AbortedState,
    NormalTerminationState,
    AbnormalTerminationState,
    ErrorWhileReadingState
)
from .summarizer import Summarizer
from .log_resource_summarizer import LogResourceSummarizer, LogResources
from .time_summarizer import TimeSummarizer, TimeManager
from .node_summarizer import NodeSummarizer, SingleNodeJob
from .error_event_summarizer import ErrorEventSummarizer, LogfileErrorEvents
from ..summarized_condor_logs.summarized_condor_logs import (
    SummarizedCondorLogs
)


class CondorLogSummarizer(Summarizer, ABC):
    """
    Abstract HTCondor log summarize class.
    For each state there should be a summarizer with the ability to summarize
    the data provided for that state.

    :param condor_logs: log files with that state
    :param state: the state
    """

    def __init__(self, condor_logs, state=None):
        self.condor_logs = condor_logs
        self.state = state
        resources, time_managers, job_details, logfiles_error_events = (
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
        self.node_summarizer = NodeSummarizer(job_details)
        self.error_event_summarizer = ErrorEventSummarizer(
            logfiles_error_events
        )

    def _get_data(self) -> (
            List[LogResources],
            List[TimeManager],
            List[JobDetails],
            List[LogfileErrorEvents]
    ):
        """Returns tuple of relevant data."""
        resources = []
        time_managers = []
        nodes = []
        log_files_error_events = []
        for condor_log in self.condor_logs:
            resources.append(condor_log.job_details.resources)
            time_managers.append(condor_log.job_details.time_manager)
            nodes.append(
                SingleNodeJob(
                    condor_log.job_details.host_address,
                    condor_log.job_details.job_times
                )
            )
            log_files_error_events.append(condor_log.logfile_error_events)

        return resources, time_managers, nodes, log_files_error_events

    @abstractmethod
    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""

    @property
    def n_jobs(self) -> int:
        """Returns number of jobs."""
        return len(self.condor_logs)


class NormalTerminationStateSummarizer(CondorLogSummarizer):
    """Summarizer for NormalTerminationState."""

    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs, NormalTerminationState())

    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""
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
    """
    Summarizer for AbnormalTerminationState.
    Does not differ form NormalTerminationStateSummarizer for now.
    """

    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs)
        self.state = AbnormalTerminationState()


class WaitingStateSummarizer(CondorLogSummarizer):
    """Summarizer for WaitingState."""

    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs, WaitingState())

    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""
        avg_times = self.time_summarizer.summarize()
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_error_states=summarized_error_states
        )


class RunningStateSummarizer(CondorLogSummarizer):
    """Summarizer for RunningState."""

    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs, RunningState())

    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""
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
    """Summarizer for AbortedState."""

    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs, AbortedState())

    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""
        avg_times = self.time_summarizer.summarize()
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            avg_times=avg_times,
            summarized_error_states=summarized_error_states
        )


class ErrorWhileReadingStateSummarizer(CondorLogSummarizer):
    """Summarizer for ErrorWhileReadingState"""
    def __init__(self, condor_logs: List[CondorLog]):
        super().__init__(condor_logs, ErrorWhileReadingState())

    def summarize(self) -> SummarizedCondorLogs:
        """Summarize."""
        summarized_error_states = self.error_event_summarizer.summarize()
        return SummarizedCondorLogs(
            self.state,
            self.n_jobs,
            summarized_error_states=summarized_error_states
        )
