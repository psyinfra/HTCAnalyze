"""Condor Event Handler."""

import os
import re
import logging
import numpy as np
from typing import List, Union
from datetime import datetime as date_time

from htcondor import (
    JobEventLog,
    JobEventType as jet,
    JobEvent as HTCJobEvent
)
from .states import *
from .job_events import (
    JobEvent,
    ErrorEvent,
    JobSubmissionEvent,
    JobExecutionEvent,
    JobTerminationEvent,
    JobAbortedEvent,
    JobAbortedBeforeExecutionEvent,
    JobAbortedBeforeSubmissionEvent,
    JobHeldEvent,
    ImageSizeEvent,
    ShadowExceptionEvent
)
from ..condor_log.logresource import (
    LogResources,
    CPULogResource,
    DiskLogResource,
    MemoryLogResource,
    GPULogResource
)
from htcanalyze.globals import STRP_FORMAT


class ReadLogException(Exception):
    """Exception raised for failed login.
    :param message: Error description message
    """

    def __init__(self, message):
        super().__init__(message)


def event_decorator(func):
    def wrapper(self, event, *args, **kwargs):
        self._event_number = event.get('EventTypeNumber')
        self._time_stamp = date_time.strptime(
            event.get('EventTime'),
            STRP_FORMAT
        )
        return func(self, event, *args, **kwargs)

    return wrapper


class EventHandler:
    _event_number = None
    _time_stamp = None

    def __init__(self):
        self._state: Union[JobState, None] = None

    @event_decorator
    def get_submission_event(self, event) -> JobEvent:
        assert event.type == jet.SUBMIT

        match_from_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get('SubmitHost')
        )
        if match_from_host:
            submitted_host = match_from_host[1]
            self._state = WaitingState()
            return JobSubmissionEvent(
                self._event_number,
                self._time_stamp,
                submitted_host
            )
        # else ERROR
        reason = "Can't read user address"
        self._state = ErrorWhileReadingState()
        return ErrorEvent(
            self._event_number,
            None,
            InvalidUserAddressState(),
            reason
        )

    @property
    def state(self):
        return self._state

    @event_decorator
    def get_execution_event(self, event, rdns_lookup=False) -> JobEvent:
        assert event.type == jet.EXECUTE
        match_to_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get('ExecuteHost')
        )
        if match_to_host:
            execution_host = match_to_host[1]
            self._state = RunningState()
            return JobExecutionEvent(
                self._event_number,
                self._time_stamp,
                execution_host,
                rdns_lookup
            )
        # ERROR
        else:
            reason = "Can't read host address"
            self._state = ErrorWhileReadingState()
            return ErrorEvent(
                self._event_number,
                None,
                InvalidHostAddressState(),
                reason
            )

    @event_decorator
    def get_job_terminated_event(self, event) -> JobEvent:

        # get all resources, replace by np.nan if value is None
        cpus_usage = event.get('CpusUsage', np.nan)
        cpus_requested = event.get('RequestCpus', np.nan)
        cpus_allocated = event.get('Cpus', np.nan)
        disk_usage = event.get('DiskUsage', np.nan)
        disk_requested = event.get('RequestDisk', np.nan)
        disk_allocated = event.get("Disk", np.nan)
        memory_usage = event.get('MemoryUsage', np.nan)
        memory_requested = event.get('RequestMemory', np.nan)
        memory_allocated = event.get('Memory', np.nan)
        gpus_usage = event.get("GpusUsage", np.nan)
        gpus_requested = event.get("RequestGpus", np.nan)
        gpus_allocated = event.get('Gpus', np.nan)

        # create list with resources
        resources = LogResources(
            CPULogResource(
                cpus_usage,
                cpus_requested,
                cpus_allocated
            ),
            DiskLogResource(
                disk_usage,
                disk_requested,
                disk_allocated
            ),
            MemoryLogResource(
                memory_usage,
                memory_requested,
                memory_allocated
            ),
            GPULogResource(
                gpus_usage,
                gpus_requested,
                gpus_allocated

            )
        )

        normal_termination = event.get('TerminatedNormally')

        # differentiate between normal and abnormal termination
        if normal_termination:
            state = NormalTerminationState()

            return_value = event.get('ReturnValue')
        else:
            state = AbnormalTerminationState()
            return_value = event.get('TerminatedBySignal')
            # Todo: include description when possible

        self._state = state
        return JobTerminationEvent(
            self._event_number,
            self._time_stamp,
            resources,
            state,
            return_value
        )

    @event_decorator
    def get_job_aborted_event(self, event) -> JobEvent:
        assert event.type == jet.JOB_ABORTED
        reason = event.get('Reason')
        if not self._state:
            aborted_event = JobAbortedBeforeSubmissionEvent(
                self._event_number,
                self._time_stamp,
                reason
            )
        elif self._state == WaitingState():
            aborted_event = JobAbortedBeforeExecutionEvent(
                self._event_number,
                self._time_stamp,
                reason
            )
        else:
            aborted_event = JobAbortedEvent(
                self._event_number,
                self._time_stamp,
                reason
            )
        self._state = AbortedState()
        return aborted_event

    @event_decorator
    def get_image_size_event(self, event) -> JobEvent:
        assert event.type == jet.IMAGE_SIZE
        size_update = event.get('Size')
        memory_usage = event.get('MemoryUsage')
        resident_set_size = event.get('ResidentSetSize')
        return ImageSizeEvent(
            self._event_number,
            self._time_stamp,
            size_update,
            memory_usage,
            resident_set_size
        )

    @event_decorator
    def get_job_held_event(self, event) -> JobEvent:
        assert event.type == jet.JOB_HELD
        reason = event.get('HoldReason')
        return JobHeldEvent(
            self._event_number,
            self._time_stamp,
            reason
        )

    @event_decorator
    def get_shadow_exception_event(self, event) -> JobEvent:
        assert event.type == jet.SHADOW_EXCEPTION
        reason = event.get('Message')
        return ShadowExceptionEvent(
            self._event_number,
            self._time_stamp,
            reason
        )

    def get_events(self, file, sec: int = 0) -> iter(List[HTCJobEvent]):

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
            raise ReadLogException(reason)

    def get_job_event(
            self,
            event: HTCJobEvent,
            rdns_lookup: bool = False
    ) -> JobEvent:
        if event.type == jet.SUBMIT:
            job_event = self.get_submission_event(event)

        elif event.type == jet.EXECUTE:
            job_event = self.get_execution_event(
                event,
                rdns_lookup=rdns_lookup
            )

        elif event.type == jet.IMAGE_SIZE:
            job_event = self.get_image_size_event(event)

            # update resource dict and termination date
        elif event.type == jet.JOB_TERMINATED:
            job_event = self.get_job_terminated_event(event)

            # update error dict and termination date
        elif event.type == jet.JOB_ABORTED:
            job_event = self.get_job_aborted_event(event)

            # update error dict
        elif event.type == jet.JOB_HELD:
            job_event = self.get_job_held_event(event)

            # update error dict
        elif event.type == jet.SHADOW_EXCEPTION:
            job_event = self.get_shadow_exception_event(event)

        else:
            raise AttributeError(f"Event type: {event.type} not handled yet")

        return job_event

