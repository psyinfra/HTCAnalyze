"""Module with wrapper classes for HTCondor Job Events."""
from datetime import datetime as date_time

from htcanalyze import ReprObject
from .node_cache import NodeCache
from .states import (
    TerminationState,
    ErrorState,
    AbortedState,
    ShadowExceptionState,
    JobHeldState
)


class DateTimeWrapper(date_time):
    """Wrapper for datetime objects to create a representation __repr__."""

    def __new__(cls, time_stamp, *_, **__):
        new = date_time.__new__(
            cls,
            year=time_stamp.year,
            month=time_stamp.month,
            day=time_stamp.day,
            hour=time_stamp.hour,
            minute=time_stamp.minute,
            second=time_stamp.second,
            microsecond=time_stamp.microsecond,
            tzinfo=time_stamp.tzinfo,
            fold=time_stamp.fold
        )
        return new

    @property
    def __dict__(self):
        return str(self)

    def __repr__(self):
        return str(self)


class JobEvent(ReprObject):
    """
    Job event represents a HTCondor JobEvent.

    Each event hat an event number and a time stamp

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
        self.time_stamp = DateTimeWrapper(time_stamp) if time_stamp else None


class JobSubmissionEvent(JobEvent):
    """
    Job submission event.

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


class ImageSizeEvent(JobEvent):
    """
    Image size event.
    Used for ram histograms.

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


class JobTerminationEvent(JobEvent):
    """
    Job termination event.

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
            termination_state: TerminationState = None,
            return_value: int = None

    ):
        super().__init__(event_number, time_stamp)
        self.resources = resources
        self.termination_state = termination_state
        self.return_value = return_value


class ErrorEvent(JobEvent):
    """
    Error event.

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
            reason: str
    ):
        super().__init__(event_number, time_stamp)
        assert isinstance(error_state, ErrorState)
        self.error_state = error_state
        self.reason = reason


class JobAbortedEvent(ErrorEvent, JobTerminationEvent):
    """
    Job aborted event.

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


class JobHeldEvent(ErrorEvent):
    """
    Job held event.

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


class ShadowExceptionEvent(ErrorEvent):
    """
    Shadow exception event.

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
