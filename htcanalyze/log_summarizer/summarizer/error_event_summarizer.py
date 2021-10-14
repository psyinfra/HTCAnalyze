from typing import List

from .summarizer import Summarizer
from ..summarized_condor_logs import SummarizedErrorState
from htcanalyze.log_analyzer.condor_log import LogfileErrorEvents
from htcanalyze.log_analyzer.event_handler import ErrorEvent
from htcanalyze.log_analyzer.event_handler.states import ErrorState


class ErrorEventCollection:
    def __init__(self, error_state: ErrorState):
        self.error_state = error_state
        self.error_events: List[ErrorEvent] = []

    def add_error_event(self, error_event: ErrorEvent):
        assert error_event.error_state == self.error_state
        self.error_events.append(error_event)


class ErrorEventManager:

    def __init__(self):
        self.error_dict = {}

    def add_events(self, log_file_error_events: LogfileErrorEvents):
        for error_event in log_file_error_events.error_events:
            err_st = error_event.error_state
            try:
                self.error_dict[err_st].add_error_event(error_event)
            except KeyError:
                self.error_dict[err_st] = ErrorEventCollection(err_st)
                self.error_dict[err_st].add_error_event(error_event)

    @property
    def error_event_collections(self) -> List[ErrorEventCollection]:
        return list(self.error_dict.values())


class ErrorEventSummarizer(Summarizer):

    def __init__(self, log_files_error_events: List[LogfileErrorEvents]):
        self.log_files_error_events = log_files_error_events

    def summarize(self) -> List[SummarizedErrorState]:
        error_event_manager = ErrorEventManager()
        for log_file_error_events in self.log_files_error_events:
            error_event_manager.add_events(log_file_error_events)

        return [
            SummarizedErrorState(eec.error_state, eec.error_events)
            for eec in error_event_manager.error_event_collections
        ]
