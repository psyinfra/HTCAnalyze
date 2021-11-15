from htcanalyze import ReprObject

import json

class LogfileErrorEvents(ReprObject):
    """
    Represents a list of error events from one single log file.

    :param error_events:
    :param file:
    """
    def __init__(self, error_events, file: str = None):
        self.error_events = error_events
        self.file = file
