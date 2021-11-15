"""Module for submission, execution and termination events."""

from datetime import datetime
from htcanalyze import ReprObject
from .states import TerminationState
from .job_events import (
    JobSubmissionEvent,
    JobExecutionEvent,
    JobTerminationEvent
)


class SETEvents(ReprObject):
    """
    Submission, Execution and Termination Events (SET-Events)
    """

    def __init__(
            self,
            submission_event: JobSubmissionEvent,
            execution_event: JobExecutionEvent,
            termination_event: JobTerminationEvent
    ):
        self.submission_event = submission_event
        self.execution_event = execution_event
        self.termination_event = termination_event

    @property
    def submission_date(self) -> datetime:
        """Returns submission date"""
        return (
            self.submission_event.time_stamp
            if self.submission_event else None
        )

    @property
    def execution_date(self) -> datetime:
        """Returns execution date."""
        return (
            self.execution_event.time_stamp
            if self.execution_event else None
        )

    @property
    def termination_date(self):
        """Returns termination date."""
        return (
            self.termination_event.time_stamp
            if self.termination_event else None
        )

    @property
    def submitter_address(self) -> str:
        """Returns submitter address of the job."""
        return (
            self.submission_event.submitter_address
            if self.submission_event else None
        )

    @property
    def host_address(self):
        """Returns host address of execution node."""
        return (
            self.execution_event.host_address
            if self.execution_event else None
        )

    @property
    def termination_state(self) -> TerminationState:
        """Returns the termination state of the job."""
        return (
            self.termination_event.termination_state
            if self.termination_event else None
        )

    @property
    def return_value(self) -> int:
        """Returns the return value of the job."""
        return (
            self.termination_event.return_value
            if self.termination_event else None
        )

    @property
    def resources(self):
        """Returns job resources."""
        return (
            self.termination_event.resources
            if self.termination_event else None
        )

    def is_empty(self):
        """Returns True if all events are None."""
        return not (
            self.submission_event or
            self.execution_event or
            self.termination_event
        )
