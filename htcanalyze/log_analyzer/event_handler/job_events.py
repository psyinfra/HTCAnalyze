"""Module with wrapper classes for HTCondor Job Events."""
from abc import ABC
from datetime import datetime as date_time

from htcanalyze import ReprObject
from .node_cache import NodeCache
from .states import (
    TerminationState,
    NormalTerminationState,
    AbnormalTerminationState,
    ErrorState,
    AbortedState,
    ShadowExceptionState,
    JobSuspendedState,
    JobHeldState,
    JobEvictedState,
    ExecutableErrorState,
    JobReconnectFailedState,
    JobDisconnectedState
)


class JobEvent(ReprObject, ABC):
    """
    Abstract class to wrap each HTCondor JobEvent.

    Each event has an event number and a time stamp
    The event number is defined by HTCondor but kept dynamic here to
    avoid errors if the setup changes.
    https://htcondor.readthedocs.io/en/latest/codes-other-values

    :param event_number: int
        HTCondor event number
    :param time_stamp: date_time
        time stamp of event
    """

    def __init__(
            self,
            event_number: int = None,
            time_stamp: date_time = None
    ):
        self.event_number = event_number
        self.time_stamp = time_stamp


class ErrorEvent(JobEvent, ABC):
    """
    Abstract class to classify error events.

    :param event_number:
    :param time_stamp:
    :param error_state:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            error_state: ErrorState,
            reason: str = None
    ):
        super().__init__(event_number, time_stamp)
        assert isinstance(error_state, ErrorState)
        self.error_state = error_state
        self.reason = reason


class JobSubmissionEvent(JobEvent):
    """
    Job submission event.

    Event Number: 000
    Event Name: Job submitted
    Event Description: This event occurs when a user submits a job.
        It is the first event you will see for a job,
        and it should only occur once.

    :param event_number:
    :param time_stamp:
    :param submitter_address:
    """
    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            submitter_address=None
    ):
        super().__init__(event_number, time_stamp)
        self.submitter_address = submitter_address

    @property
    def __dict__(self):
        return {
            "event_number": self.event_number,
            "time_stamp": str(self.time_stamp),
            "submitter_address": self.submitter_address
        }


class JobExecutionEvent(JobEvent):
    """
    Job execution event.

    Event Number: 001
    Event Name: Job executing
    Event Description: This shows up when a job is running.
        It might occur more than once.

    :param event_number:
    :param time_stamp:
    :param host_address:
    :param rdns_lookup:
    """

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            host_address=None,
            rdns_lookup=False
    ):

        super().__init__(event_number, time_stamp)
        self.host_address = (
            NodeCache().get_host_by_addr_cached(host_address)
            if rdns_lookup else host_address
        )


class ExecutableErrorEvent(ErrorEvent):
    """
    Error in executable event.

    Event Number: 002
    Event Name: Error in executable
    Event Description: The job could not be run because the executable was bad.

    :param event_number:
    :param time_stamp:
    :param reason:
    """
    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            ExecutableErrorState(),
            reason
        )


class JobCheckpointedEvent(JobEvent):
    """
    Error in executable event.

    Event Number: 003
    Event Name: Job was checkpointed
    Event Description: The job’s complete state was written to a checkpoint
        file. This might happen without the job being removed from a machine,
        because the checkpointing can happen periodically.

    """
    # Todo: figure out data load


class JobEvictedEvent(ErrorEvent):
    """
    Job evicted event.

    Event Number: 004
    Event Name: Job evicted from machine
    Event Description: A job was removed from a machine before it finished,
        usually for a policy reason. Perhaps an interactive user has
        claimed the computer, or perhaps another job is higher priority.

    """
    def __init__(
            self,
            event_number,
            time_stamp,
            checkpointed=False,
    ):
        if checkpointed:
            message = (
                "Job evicted with checkpoint, "
                "continue process on last checkpoint"
            )
        else:
            message = (
                "Job evicted, progress is lost, "
                "job goes back into the queue"
            )

        super().__init__(
            event_number,
            time_stamp,
            JobEvictedState(),
            message
        )


class JobTerminationEvent(JobEvent, ABC):
    """
    Job termination event.

    Event Number: 005
    Event Name: Job terminated
    Event Description: The job has completed.

    :param event_number:
    :param time_stamp:
    :param resources:
    :param termination_state:
    :param return_value:
    """

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            resources=None,
            return_value: int = None,
            termination_state: TerminationState = None
    ):
        super().__init__(event_number, time_stamp)
        self.resources = resources
        self.return_value = return_value
        self.termination_state = termination_state


class NormalTerminationEvent(JobTerminationEvent):
    """Normal Termination Event."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            termination_state=NormalTerminationState()
        )


class AbnormalTerminationEvent(JobTerminationEvent):
    """Abnormal Termination Event."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            termination_state=AbnormalTerminationState()
        )


class ImageSizeEvent(JobEvent):
    """
    Image size event.
    Used for ram histograms.

    Event Number: 006
    Event Name: Image size of job updated
    Event Description: An informational event, to update the amount
        of memory that the job is using while running.
        It does not reflect the state of the job.

    :param event_number:
    :param time_stamp:
    :param size_update:
    :param memory_usage:
    :param resident_set_size:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            size_update=None,
            memory_usage=None,
            resident_set_size=None
    ):
        super().__init__(event_number, time_stamp)
        self.size_update = size_update
        self.memory_usage = memory_usage
        self.resident_set_size = resident_set_size


class ShadowExceptionEvent(ErrorEvent):
    """
    Shadow exception event.

    Event Number: 007
    Event Name: Shadow exception
    Event Description: The condor_shadow, a program on the submit computer
        that watches over the job and performs some services for the job,
        failed for some catastrophic reason. The job will leave the machine
        and go back into the queue.

    :param event_number:
    :param time_stamp:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            ShadowExceptionState(),
            reason
        )


class JobAbortedEvent(ErrorEvent, JobTerminationEvent):
    """
    Job aborted event.

    Event Number: 009
    Event Name: Job aborted
    Event Description: The user canceled the job.

    :param event_number:
    :param time_stamp:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            AbortedState(),
            reason
        )
        self.termination_state = AbortedState()


class JobAbortedBeforeSubmissionEvent(JobAbortedEvent):
    """Job was aborted before submission event."""


class JobAbortedBeforeExecutionEvent(JobAbortedEvent):
    """Job was aborted before execution event."""


class JobSuspendedEvent(ErrorEvent):
    """
    Job suspended event.

    Event Number: 010
    Event Name: Job was suspended
    Event Description: The job is still on the computer,
        but it is no longer executing.
        This is usually for a policy reason,
        such as an interactive user using the computer.

    :param event_number:
    :param time_stamp:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            JobSuspendedState(),
            reason
        )


class JobUnsuspendedEvent(JobEvent):
    """
    Job unsuspended event.

    Event Number: 011
    Event Name: Job was unsuspended
    Event Description: The job has resumed execution,
        after being suspended earlier.
    """


class JobHeldEvent(ErrorEvent):
    """
    Job held event.

    Event Number: 012
    Event Name: Job was held
    Event Description: The job has transitioned to the hold state.
        This might happen if the user applies
        the condor_hold command to the job.

    :param event_number:
    :param time_stamp:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            JobHeldState(),
            reason
        )


class JobReleasedEvent(JobEvent):
    """
    Job was released after being hold event.

    Event Number: 013
    Event Name: Job was released
    Event Description: The job was in the hold state and is to be re-run.

    """


class JobDisconnectedEvent(ErrorEvent):
    """
    Job disconnected event.

    Event Number: 022
    Event Name: Remote system call socket lost
    Event Description: The condor_shadow and condor_starter
        (which communicate while the job runs) have lost contact.

    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            JobDisconnectedState(),
            reason
        )


class JobReconnectedEvent(JobEvent):
    """
    Job reconnected event.

    Event Number: 023
    Event Name: Remote system call socket reestablished
    Event Description: The condor_shadow and condor_starter
        (which communicate while the job runs) have been able
        to resume contact before the job lease expired.

    """


class JobReconnectFailedEvent(ErrorEvent):
    """
    Job reconnect failed event.

    Event Number: 024
    Event Name: Remote system call reconnect failure
    Event Description: The condor_shadow and condor_starter
        (which communicate while the job runs) were unable to resume
        contact before the job lease expired.

    :param event_number:
    :param time_stamp:
    :param reason:
    """

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super().__init__(
            event_number,
            time_stamp,
            JobReconnectFailedState(),
            reason
        )
