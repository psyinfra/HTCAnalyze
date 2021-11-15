"""Module to manage error events of a single log file."""
from htcanalyze import ReprObject


class LogfileErrorEvents(ReprObject):
    """
    Represents a list of error events from one single log file.

    :param error_events:
    :param file:
    """
    def __init__(self, error_events, file: str = None):
        self.error_events = error_events
        self.file = file
