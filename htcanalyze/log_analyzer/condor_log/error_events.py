
import json


class LogfileErrorEvents:

    def __init__(self, error_events):
        self.error_events = error_events

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
