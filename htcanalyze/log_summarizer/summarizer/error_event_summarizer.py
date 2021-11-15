"""Module to summarize error events."""
from typing import List

from htcanalyze.log_analyzer.condor_log.error_events import LogfileErrorEvents
from htcanalyze.log_analyzer.event_handler.job_events import ErrorEvent
from htcanalyze.log_analyzer.event_handler.states import ErrorState
from .summarizer import Summarizer
from ..summarized_condor_logs.summarized_error_events import (
    SummarizedErrorState
)


class ErrorEventCollection:
    """
    Used to collect all ErrorEvent(s) with the same ErrorState.

    :param error_state: ErrorState
    """
    def __init__(self, error_state: ErrorState):
        self.error_state = error_state
        self.error_events: List[ErrorEvent] = []
        self.files = []

    def add_error_event(self, error_event: ErrorEvent, file):
        """Add error event to collection."""
        assert error_event.error_state == self.error_state
        self.error_events.append(error_event)
        if file not in self.files:
            self.files.append(file)


class ErrorEventManager:
    """Manages error events."""

    def __init__(self):
        self.error_dict = {}

    def add_events(self, log_file_error_events: LogfileErrorEvents):
        """Add events to each collection with the same error state."""
        for error_event in log_file_error_events.error_events:
            err_st = error_event.error_state
            try:
                self.error_dict[err_st].add_error_event(
                    error_event,
                    log_file_error_events.file
                )
            except KeyError:
                self.error_dict[err_st] = ErrorEventCollection(err_st)
                self.error_dict[err_st].add_error_event(
                    error_event,
                    log_file_error_events.file
                )

    @property
    def error_event_collections(self) -> List[ErrorEventCollection]:
        """Return a list of ErrorEventCollections."""
        return list(self.error_dict.values())


class ErrorEventSummarizer(Summarizer):
    """Summarize error events."""

    def __init__(self, log_files_error_events: List[LogfileErrorEvents]):
        self.log_files_error_events = log_files_error_events

    def summarize(self) -> List[SummarizedErrorState]:
        """Returns a list of SummarizedErrorStates."""
        error_event_manager = ErrorEventManager()
        for log_file_error_events in self.log_files_error_events:
            error_event_manager.add_events(log_file_error_events)

        return [
            SummarizedErrorState(
                eec.error_state,
                eec.error_events,
                eec.files
            )
            for eec in error_event_manager.error_event_collections
        ]
