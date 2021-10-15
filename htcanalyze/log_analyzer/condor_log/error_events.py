
import json


class LogfileErrorEvents:

    def __init__(self, error_events, file: str = None):
        self.error_events = error_events
        self.file = file

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
