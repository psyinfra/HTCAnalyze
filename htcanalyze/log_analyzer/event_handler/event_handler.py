"""Condor Event Handler."""

import os
import re
import logging
import json
from typing import List, Union
from datetime import datetime as date_time

import numpy as np
from htcondor import (
    JobEventLog,
    JobEventType as jet,
    JobEvent as HTCJobEvent
)

from htcanalyze.globals import STRP_FORMAT
from .states import (
    JobState,
    RunningState,
    ErrorWhileReadingState,
    InvalidHostAddressState,
    WaitingState,
    InvalidUserAddressState,
    NormalTerminationState,
    AbnormalTerminationState,
    AbortedState
)
from .job_events import (
    JobEvent,
    ErrorEvent,
    JobSubmissionEvent,
    JobExecutionEvent,
    JobEvictedEvent,
    JobTerminationEvent,
    NormalTerminationEvent,
    AbnormalTerminationEvent,
    JobAbortedEvent,
    JobAbortedBeforeExecutionEvent,
    JobAbortedBeforeSubmissionEvent,
    JobHeldEvent,
    ImageSizeEvent,
    ShadowExceptionEvent,
    JobDisconnectedEvent,
    JobReconnectedEvent,
    JobReconnectFailedEvent
)
from ..condor_log.logresource import (
    LogResources,
    CPULogResource,
    DiskLogResource,
    MemoryLogResource,
    GPULogResource
)


class ReadLogException(Exception):
    """Can't read log file exception."""


class HTCJobEventWrapper:
    """
    Wrapper for HTCondor JobEvent.

    Extracts event number and time_stamp of an event.
    The wrapped event can be printed to the terminal for dev purpose.

    :param job_event: HTCJobEvent
    """

    def __init__(self, job_event: HTCJobEvent):

        self.wrapped_class = job_event
        self.event_number = job_event.get('EventTypeNumber')
        self.time_stamp = date_time.strptime(
                job_event.get('EventTime'),
                STRP_FORMAT
            )

    def __getattr__(self, attr):
        return getattr(self.wrapped_class, attr)

    def get(self, *args, **kwargs):
        return self.wrapped_class.get(*args, **kwargs)

    def items(self):
        return self.wrapped_class.items()

    def keys(self):
        return self.wrapped_class.keys()

    def values(self):
        return self.wrapped_class.values()

    def to_dict(self):
        return {key: val for key, val in self.items()}

    def __repr__(self):
        return json.dumps(
            self.to_dict(),
            indent=2
        )


class EventHandler:
    """Event handler to wrap HTCondor job events."""

    def __init__(self):
        self._state: Union[JobState, None] = None

    @property
    def state(self) -> JobState:
        """Returns current job state."""
        return self._state

    def get_submission_event(
            self,
            event: HTCJobEventWrapper
    ) -> Union[JobSubmissionEvent, ErrorEvent]:
        """
        Reads and returns a JobSubmissionEvent or an ErrorEvent if
        the user address was dubious.

        :param event:
        :return:
        """
        assert event.type == jet.SUBMIT

        match_from_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get("SubmitHost")
        )
        if match_from_host:
            submitted_host = match_from_host[1]
            self._state = WaitingState()
            return JobSubmissionEvent(
                event.event_number,
                event.time_stamp,
                submitted_host
            )
        # else ERROR
        reason = "Can't read user address"
        self._state = ErrorWhileReadingState()
        return ErrorEvent(
            event.event_number,
            None,
            InvalidUserAddressState(),
            reason
        )

    def get_execution_event(
            self,
            event: HTCJobEventWrapper,
            rdns_lookup: bool = False
    ) -> Union[JobExecutionEvent, ErrorEvent]:
        """
        Reads and returns a JobExecutionEvent or an ErrorEvent if
        the host address was dubious.

        :param event:
        :param rdns_lookup: bool
            Whether to reversely resolve host addresses by domain name
        :return:
        """
        assert event.type == jet.EXECUTE
        match_to_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get('ExecuteHost')
        )
        if match_to_host:
            execution_host = match_to_host[1]
            self._state = RunningState()
            return JobExecutionEvent(
                event.event_number,
                event.time_stamp,
                execution_host,
                rdns_lookup
            )
        # ERROR
        reason = "Can't read host address"
        self._state = ErrorWhileReadingState()
        return ErrorEvent(
            event.event_number,
            None,
            InvalidHostAddressState(),
            reason
        )

    def get_job_terminated_event(
            self,
            event: HTCJobEventWrapper
    ) -> JobTerminationEvent:
        """Reads and returns a JobTerminationEvent."""
        # create list with resources,
        # replace by np.nan if values are None
        resources = LogResources(
            CPULogResource(
                event.get('CpusUsage', np.nan),
                event.get('RequestCpus', np.nan),
                event.get('Cpus', np.nan)
            ),
            DiskLogResource(
                event.get('DiskUsage', np.nan),
                event.get('RequestDisk', np.nan),
                event.get("Disk", np.nan)
            ),
            MemoryLogResource(
                event.get('MemoryUsage', np.nan),
                event.get('RequestMemory', np.nan),
                event.get('Memory', np.nan)
            ),
            GPULogResource(
                event.get("GpusUsage", np.nan),
                event.get("RequestGpus", np.nan),
                event.get('Gpus', np.nan)

            )
        )

        normal_termination = event.get('TerminatedNormally')

        # differentiate between normal and abnormal termination
        if normal_termination:
            self._state = NormalTerminationState()
            return_value = event.get('ReturnValue')
            return NormalTerminationEvent(
                event.event_number,
                event.time_stamp,
                resources,
                return_value
            )
        else:
            return_value = event.get('TerminatedBySignal')
            self._state = AbnormalTerminationState()
            return AbnormalTerminationEvent(
                event.event_number,
                event.time_stamp,
                resources,
                return_value
            )
            # Todo: include description when possible

    @staticmethod
    def get_job_evicted_event(
            event: HTCJobEventWrapper
    ) -> JobEvictedEvent:
        """Reads and returns a JobEvictedEvent."""
        assert event.type == jet.JOB_EVICTED
        # Todo: figure out the data load of
        #  TerminatedNormally and TerminatedAndRequed
        return JobEvictedEvent(
            event.event_number,
            event.time_stamp,
            checkpointed=event.get("Checkpointed")
        )

    @staticmethod
    def get_image_size_event(event: HTCJobEventWrapper) -> ImageSizeEvent:
        """Reads and returns a ImageSizeEvent."""
        assert event.type == jet.IMAGE_SIZE
        size_update = event.get('Size')
        memory_usage = event.get('MemoryUsage')
        resident_set_size = event.get('ResidentSetSize')
        return ImageSizeEvent(
            event.event_number,
            event.time_stamp,
            size_update,
            memory_usage,
            resident_set_size
        )

    @staticmethod
    def get_shadow_exception_event(
            event: HTCJobEventWrapper
    ) -> ShadowExceptionEvent:
        """Reads and returns a ShadowExceptionEvent."""
        assert event.type == jet.SHADOW_EXCEPTION
        reason = event.get('Message')
        return ShadowExceptionEvent(
            event.event_number,
            event.time_stamp,
            reason
        )

    def get_job_aborted_event(
            self,
            event: HTCJobEventWrapper
    ) -> JobAbortedEvent:
        """Reads and returns a JobAbortedEvent."""
        assert event.type == jet.JOB_ABORTED
        reason = event.get('Reason')
        if not self._state:
            aborted_event = JobAbortedBeforeSubmissionEvent(
                event.event_number,
                event.time_stamp,
                reason
            )
        elif self._state == WaitingState():
            aborted_event = JobAbortedBeforeExecutionEvent(
                event.event_number,
                event.time_stamp,
                reason
            )
        else:
            aborted_event = JobAbortedEvent(
                event.event_number,
                event.time_stamp,
                reason
            )
        self._state = AbortedState()
        return aborted_event

    @staticmethod
    def get_job_held_event(event: HTCJobEventWrapper) -> JobHeldEvent:
        """Reads and returns a JobHeldEvent."""
        assert event.type == jet.JOB_HELD
        message = event.get('HoldReason')
        return JobHeldEvent(
            event.event_number,
            event.time_stamp,
            message
        )

    @staticmethod
    def get_job_disconnected_event(
            event: HTCJobEventWrapper
    ) -> JobDisconnectedEvent:
        assert event.type == jet.JOB_DISCONNECTED
        reason = f"{event.get('DisconnectReason')}"
        return JobDisconnectedEvent(
            event.event_number,
            event.time_stamp,
            reason
        )

    @staticmethod
    def get_job_reconnected_event(
            event: HTCJobEventWrapper
    ) -> JobReconnectedEvent:
        assert event.type == jet.JOB_RECONNECTED
        reason = f"{event.get('Reason')}"
        return JobReconnectedEvent(
            event.event_number,
            event.time_stamp,
            reason
        )

    @staticmethod
    def get_job_reconnect_failed_event(
            event: HTCJobEventWrapper
    ) -> JobReconnectFailedEvent:
        assert event.type == jet.JOB_RECONNECT_FAILED
        reason = f"{event.get('Reason')}"
        return JobReconnectFailedEvent(
            event.event_number,
            event.time_stamp,
            reason
        )

    def get_job_event(
            self,
            event: HTCJobEvent,
            rdns_lookup: bool = False
    ) -> JobEvent:
        """
        Takes a HTCondor job event and returns an own wrapped JobEvent class.

        :param event: HTCJobEvent
            A job event from the HTCondor python bindings.
        :param rdns_lookup: bool
            Whether to reversely resolve host addresses by domain name
        :return: JobEvent
            Wrapped JobEvent class with own properties
        """
        wrapped_job_event = HTCJobEventWrapper(event)
        if wrapped_job_event.type == jet.SUBMIT:
            return self.get_submission_event(wrapped_job_event)

        if wrapped_job_event.type == jet.EXECUTE:
            return self.get_execution_event(
                wrapped_job_event,
                rdns_lookup=rdns_lookup
            )

        if wrapped_job_event.type == jet.JOB_EVICTED:
            return self.get_job_evicted_event(wrapped_job_event)

        if wrapped_job_event.type == jet.JOB_TERMINATED:
            return self.get_job_terminated_event(wrapped_job_event)

        if wrapped_job_event.type == jet.IMAGE_SIZE:
            return self.get_image_size_event(wrapped_job_event)

        if wrapped_job_event.type == jet.SHADOW_EXCEPTION:
            return self.get_shadow_exception_event(wrapped_job_event)

        if wrapped_job_event.type == jet.JOB_ABORTED:
            return self.get_job_aborted_event(wrapped_job_event)

        if wrapped_job_event.type == jet.JOB_HELD:
            return self.get_job_held_event(wrapped_job_event)

        if wrapped_job_event.type == jet.JOB_DISCONNECTED:
            return self.get_job_disconnected_event(wrapped_job_event)

        if wrapped_job_event.type == jet.JOB_RECONNECT_FAILED:
            return self.get_job_reconnect_failed_event(wrapped_job_event)

        # else:
        raise AttributeError(
            f"Event type: {wrapped_job_event.type} not handled yet"
        )

    def get_htc_events(
            self,
            file: str,
            sec: int = 0
    ) -> iter(List[HTCJobEvent]):
        """
        Returns a generator over HTCondor job events.
        :param file: HTCondor log file
        :param sec: seconds to wait for new events
        :return: list of HTCondor job events
        """
        jel = JobEventLog(file)

        try:
            # Read all currently-available events
            # waiting for 'sec' seconds for the next event.
            events = jel.events(sec)
            for event in events:
                yield event

        except OSError as err:
            logging.exception(err)
            file_name = os.path.basename(file)
            if err.args[0] == "ULOG_RD_ERROR":
                reason = (
                    f"File was manipulated or contains gpu data: {file_name}"
                )
            else:
                reason = f"Not able to open the file: {file_name}"

            self._state = ErrorWhileReadingState()
            raise ReadLogException(reason) from err
