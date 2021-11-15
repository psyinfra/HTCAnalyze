"""Save HTCondor job execution details."""
import json

from htcanalyze import ReprObject
from ..event_handler.set_events import SETEvents
from ..event_handler.states import JobState
from .time_manager import TimeManager


class JobDetails(ReprObject):
    """
    Class to store and manage the different job details.

    Mostly the complexity lies in creating
    colored output depending on the states
    """

    def __init__(
            self,
            set_events: SETEvents,
            state: JobState

    ):
        self.set_events = set_events
        self.time_manager = TimeManager.from_set_events(set_events)
        self.state = state

    @property
    def resources(self):
        return self.set_events.resources

    @property
    def host_address(self):
        return self.set_events.host_address

    @property
    def submitter_address(self):
        return self.set_events.submitter_address

    @property
    def job_times(self):
        return self.time_manager.job_times
