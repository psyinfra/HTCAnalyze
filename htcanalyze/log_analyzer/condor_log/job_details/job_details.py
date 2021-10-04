"""Save HTCondor job execution details."""
import json

# from event_handler.state_manager import StateManager
# from event_handler.set_events import SETEvents
from .time_manager import TimeManager


class JobDetails:
    """
    Class to store and manage the different job details.

    Mostly the complexity lies in creating
    colored output depending on the states
    """

    def __init__(
            self,
            set_events,
            state_manager

    ):
        self.set_events = set_events
        self.time_manager = TimeManager(set_events)
        self.state_manager = state_manager

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
