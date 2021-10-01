
from enum import Enum

from .host_nodes import node_cache


class ReadLogException(Exception):
    """Exception raised for failed login.
    :param error_code: Error code
    :param message: Error description message
    """

    def __init__(self, message):
        super().__init__(message)


class JobState(Enum):
    NORMAL_TERMINATION = 0
    ABNORMAL_TERMINATION = 1
    WAITING = 2
    RUNNING = 3
    ERROR_WHILE_READING = 4
    ABORTED = 5
    JOB_HELD = 6
    SHADOW_EXCEPTION = 7
    UNKNOWN = 8


class JobEvent:

    def __init__(
            self,
            event_number=None,
            time_stamp=None
    ):
        self.event_number = event_number
        self.time_stamp = time_stamp


class JobSubmissionEvent(JobEvent):

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            submitted_by=None
    ):
        super(JobSubmissionEvent, self).__init__(event_number, time_stamp)
        self.submitted_by = submitted_by


class JobExecutionEvent(JobEvent):

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            executing_on=None,
            rdns_lookup=False
    ):
        super(JobExecutionEvent, self).__init__(event_number, time_stamp)
        self.executing_on = (
            node_cache.get_host_by_addr_cached(executing_on)
            if rdns_lookup else executing_on
        )


class ImageSizeEvent(JobEvent):

    def __init__(
            self,
            event_number,
            time_stamp,
            size_update=None,
            memory_usage=None,
            resident_set_size=None
    ):
        super(ImageSizeEvent, self).__init__(event_number, time_stamp)
        self.size_update = size_update
        self.memory_usage = memory_usage
        self.resident_set_size = resident_set_size


class JobTerminationEvent(JobEvent):

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            resources=None,
            termination_state: JobState = None,
            return_value: int = None

    ):
        super(JobTerminationEvent, self).__init__(event_number, time_stamp)
        self.resources = resources
        self.termination_state = termination_state
        self.return_value = return_value


class ErrorEvent(JobEvent):

    class ErrorCode(Enum):
        ABORTED = JobState.ABORTED
        JOB_HELD = JobState.JOB_HELD
        SHADOW_EXCEPTION = JobState.SHADOW_EXCEPTION

    def __init__(
            self,
            event_number,
            time_stamp,
            error_code: ErrorCode,
            reason
    ):
        super(ErrorEvent, self).__init__(event_number, time_stamp)
        assert error_code == ErrorEvent.ErrorCode
        self.error_code = error_code
        self.reason = reason


class JobAbortedEvent(ErrorEvent, JobTerminationEvent):

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super(JobAbortedEvent, self).__init__(
            event_number,
            time_stamp,
            JobState.ABORTED,
            reason
        )
        self.termination_state = JobState.ABORTED


class JobHeldEvent(ErrorEvent):

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super(JobHeldEvent, self).__init__(
            event_number,
            time_stamp,
            ErrorEvent.ErrorCode.JOB_HELD,
            reason
        )


class ShadowExceptionEvent(ErrorEvent):

    def __init__(
            self,
            event_number,
            time_stamp,
            reason
    ):
        super(ShadowExceptionEvent, self).__init__(
            event_number,
            time_stamp,
            ErrorEvent.ErrorCode.SHADOW_EXCEPTION,
            reason

        )

