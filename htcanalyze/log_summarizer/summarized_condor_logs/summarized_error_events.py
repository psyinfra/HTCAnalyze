
import json
from typing import List
from htcanalyze.log_analyzer.event_handler.job_events import ErrorEvent
from htcanalyze.log_analyzer.event_handler.states import ErrorState


class SummarizedErrorState:

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

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )

    def __lt__(self, other):
        return self.n_error_events < other.n_error_events
