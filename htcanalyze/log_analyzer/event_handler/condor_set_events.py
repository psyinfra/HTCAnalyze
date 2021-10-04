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

        self.submitter_address = (
            submission_event.submitter_address if submission_event else None
        )

        self.host_address = (
            execution_event.host_address if execution_event else None
        )

        self.return_value = (
            termination_event.return_value if termination_event else None
        )

    @property
    def submission_date(self):
        return (
            self.submission_event.time_stamp
            if self.submission_event else None
        )

    @property
    def execution_date(self):
        return (
            self.execution_event.time_stamp
            if self.execution_event else None
        )

    @property
    def termination_date(self):
        return (
            self.termination_event.time_stamp
            if self.termination_event else None
        )

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
