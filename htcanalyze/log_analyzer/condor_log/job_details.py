"""Save HTCondor job execution details."""

from htcanalyze import ReprObject
from ..event_handler.set_events import SETEvents
from ..event_handler.states import JobState
from .time_manager import TimeManager, JobTimes
from .logresource import LogResources


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
    def resources(self) -> LogResources:
        """Returns log resources."""
        return self.set_events.resources

    @property
    def host_address(self) -> str:
        """Returns host address."""
        return self.set_events.host_address

    @property
    def submitter_address(self) -> str:
        """Returns submitter address."""
        return self.set_events.submitter_address

    @property
    def job_times(self) -> JobTimes:
        """Returns job times."""
        return self.time_manager.job_times
