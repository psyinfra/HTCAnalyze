"""Condor Event Handler."""

import os
import re
import logging
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


class ReadLogException(Exception):
    """Can't read log file exception."""


class WrappedHTCJobEvent(HTCJobEvent):
    """Wrapper for HTCJobEvent."""

    def __new__(cls, job_event: HTCJobEvent):
        new = job_event
        new.event_number = job_event.get('EventTypeNumber')
        new.time_stamp = date_time.strptime(
            job_event.get('EventTime'),
            STRP_FORMAT
        )
        return new


class EventHandler:
    """Event handler to wrap HTCondor job events."""

    def __init__(self):
        self._state: Union[JobState, None] = None

    def get_submission_event(
            self,
            event: WrappedHTCJobEvent
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
            event.get('SubmitHost')
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

    @property
    def state(self) -> JobState:
        """Returns current job state."""
        return self._state

    def get_execution_event(
            self,
            event: WrappedHTCJobEvent,
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
            event: WrappedHTCJobEvent
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
            state = NormalTerminationState()

            return_value = event.get('ReturnValue')
        else:
            state = AbnormalTerminationState()
            return_value = event.get('TerminatedBySignal')
            # Todo: include description when possible

        self._state = state
        return JobTerminationEvent(
            event.event_number,
            event.time_stamp,
            resources,
            state,
            return_value
        )

    def get_job_aborted_event(
            self,
            event: WrappedHTCJobEvent
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
    def get_image_size_event(event: WrappedHTCJobEvent) -> ImageSizeEvent:
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
    def get_job_held_event(event: WrappedHTCJobEvent) -> JobHeldEvent:
        """Reads and returns a JobHeldEvent."""
        assert event.type == jet.JOB_HELD
        reason = event.get('HoldReason')
        return JobHeldEvent(
            event.event_number,
            event.time_stamp,
            reason
        )

    @staticmethod
    def get_shadow_exception_event(
            event: WrappedHTCJobEvent
    ) -> ShadowExceptionEvent:
        """Reads and returns a ShadowExceptionEvent."""
        assert event.type == jet.SHADOW_EXCEPTION
        reason = event.get('Message')
        return ShadowExceptionEvent(
            event.event_number,
            event.time_stamp,
            reason
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
        wrapped_job_event = WrappedHTCJobEvent(event)
        if wrapped_job_event.type == jet.SUBMIT:
            job_event = self.get_submission_event(wrapped_job_event)

        elif wrapped_job_event.type == jet.EXECUTE:
            job_event = self.get_execution_event(
                wrapped_job_event,
                rdns_lookup=rdns_lookup
            )

        elif wrapped_job_event.type == jet.IMAGE_SIZE:
            job_event = self.get_image_size_event(wrapped_job_event)

            # update resource dict and termination date
        elif wrapped_job_event.type == jet.JOB_TERMINATED:
            job_event = self.get_job_terminated_event(wrapped_job_event)

            # update error dict and termination date
        elif wrapped_job_event.type == jet.JOB_ABORTED:
            job_event = self.get_job_aborted_event(wrapped_job_event)

            # update error dict
        elif wrapped_job_event.type == jet.JOB_HELD:
            job_event = self.get_job_held_event(wrapped_job_event)

            # update error dict
        elif wrapped_job_event.type == jet.SHADOW_EXCEPTION:
            job_event = self.get_shadow_exception_event(wrapped_job_event)

        else:
            raise AttributeError(
                f"Event type: {wrapped_job_event.type} not handled yet"
            )

        return job_event
