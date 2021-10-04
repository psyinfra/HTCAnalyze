import json

from .condor_job_events import JobSubmissionEvent, JobExecutionEvent, \
    JobTerminationEvent


class SETEvents:
    """
    Submission, Execution and Termination Events, (SET-Events)
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
    def submission_date(self):
        return (
            self.submission_event.time_stamp
            if self.submission_event else None
        )

    @property
    def submitter_address(self):
        return (
            self.submission_event.submitter_address
            if self.submission_event else None
        )

    @property
    def execution_date(self):
        return (
            self.execution_event.time_stamp
            if self.execution_event else None
        )

    @property
    def host_address(self):
        return (
            self.execution_event.host_address
            if self.execution_event else None
        )

    @property
    def termination_date(self):
        return (
            self.termination_event.time_stamp
            if self.termination_event else None
        )

    @property
    def termination_state(self):
        return (
            self.termination_event.termination_state
            if self.termination_event else None
        )

    @property
    def return_value(self):
        return (
            self.termination_event.return_value
            if self.termination_event else None
        )

    @property
    def resources(self):
        return (
            self.termination_event.resources
            if self.termination_event else None
        )

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
