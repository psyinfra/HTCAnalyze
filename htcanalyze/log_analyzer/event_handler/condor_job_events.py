
import json
from enum import Enum
from datetime import datetime as date_time

from .host_nodes import node_cache


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

    @property
    def __dict__(self):
        return {
            "name": self.name,
            "value": self.value
        }


class DateTimeWrapper(date_time):

    def __new__(cls, time_stamp):
        new = date_time.__new__(
            cls,
            year=time_stamp.year,
            month=time_stamp.month,
            day=time_stamp.day,
            hour=time_stamp.hour,
            minute=time_stamp.minute,
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


class JobEvent:

    def __init__(
            self,
            event_number=None,
            time_stamp=None
    ):
        self.event_number = event_number
        self.time_stamp = DateTimeWrapper(time_stamp)

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )


class JobSubmissionEvent(JobEvent):

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            submitter_address=None
    ):
        super(JobSubmissionEvent, self).__init__(event_number, time_stamp)
        self.submitter_address = submitter_address

    @property
    def __dict__(self):
        return {
            "event_number": self.event_number,
            "time_stamp": str(self.time_stamp),
            "submitter_address": self.submitter_address
        }


class JobExecutionEvent(JobEvent):

    def __init__(
            self,
            event_number=None,
            time_stamp=None,
            host_address=None,
            rdns_lookup=False
    ):
        super(JobExecutionEvent, self).__init__(event_number, time_stamp)
        self.host_address = (
            node_cache.get_host_by_addr_cached(host_address)
            if rdns_lookup else host_address
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
