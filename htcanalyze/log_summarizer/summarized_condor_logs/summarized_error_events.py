"""Module to represent summarized error events."""
from typing import List

from htcanalyze import ReprObject
from htcanalyze.log_analyzer.event_handler.job_events import ErrorEvent
from htcanalyze.log_analyzer.event_handler.states import ErrorState


class SummarizedErrorState(ReprObject):
    """
    Represents summarized error states.

    :param error_state: error state
        The error state
    :param error_events: error events
        All events with that error state
    :param files: files
        All files in which this error state occurred
    """

    def __init__(
            self,
            error_state: ErrorState,
            error_events: List[ErrorEvent],
            files: List = None
    ):
        self.error_state = error_state
        self.error_events = error_events
        self.n_error_events = len(error_events)
        self.files = files

    def __lt__(self, other):
        return self.n_error_events < other.n_error_events
