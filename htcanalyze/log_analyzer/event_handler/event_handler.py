"""Condor Event Handler."""

import os
import re
import logging
import numpy as np
from typing import List

from htcondor import JobEventLog, JobEventType as jet, JobEvent as HTCJobEvent

from .state_manager import StateManager
from .job_events import *
from htcanalyze.log_analyzer.condor_log import LogResources, Resource


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
            "%Y-%m-%dT%H:%M:%S"
        )
        return func(self, event, *args, **kwargs)

    return wrapper


class EventHandler:
    _event_number = None
    _time_stamp = None

    def __init__(self):
        self.state_manager = StateManager()

    @event_decorator
    def get_submission_event(self, event) -> JobEvent:
        assert event.type == jet.SUBMIT

        match_from_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get('SubmitHost')
        )
        if match_from_host:
            submitted_host = match_from_host[1]
            self.state_manager.state = JobState.WAITING
            return JobSubmissionEvent(
                self._event_number,
                self._time_stamp,
                submitted_host
            )
        # else ERROR
        reason = "Can't read user address"
        self.state_manager.state = JobState.ERROR_WHILE_READING
        return ErrorEvent(
            self._event_number,
            None,
            ErrorState.INVALID_USER_ADDRESS,
            reason
        )

    @event_decorator
    def get_execution_event(self, event, rdns_lookup=False) -> JobEvent:
        assert event.type == jet.EXECUTE
        match_to_host = re.match(
            r"<(.+):[0-9]+\?(.*)>",
            event.get('ExecuteHost')
        )
        if match_to_host:
            execution_host = match_to_host[1]
            self.state_manager.state = JobState.RUNNING
            return JobExecutionEvent(
                self._event_number,
                self._time_stamp,
                execution_host,
                rdns_lookup
            )
        # ERROR
        else:
            reason = "Can't read host address"
            self.state_manager.state = JobState.ERROR_WHILE_READING
            return ErrorEvent(
                self._event_number,
                None,
                ErrorState.INVALID_HOST_ADDRESS,
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
            Resource(
                "Cpus",
                cpus_usage,
                cpus_requested,
                cpus_allocated
            ),
            Resource(
                "Disk (KB)",
                disk_usage,
                disk_requested,
                disk_allocated
            ),
            Resource(
                "Memory (MB)",
                memory_usage,
                memory_requested,
                memory_allocated
            ),
            Resource(
                "Gpus (Average)",
                gpus_usage,
                gpus_requested,
                gpus_allocated

            )
        )

        normal_termination = event.get('TerminatedNormally')

        # differentiate between normal and abnormal termination
        if normal_termination:
            state = JobState.NORMAL_TERMINATION

            return_value = event.get('ReturnValue')
        else:
            state = JobState.ABNORMAL_TERMINATION
            return_value = event.get('TerminatedBySignal')
            # Todo: include description when possible

        self.state_manager.state = state
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
        self.state_manager.state = JobState.ABORTED
        return JobAbortedEvent(
            self._event_number,
            self._time_stamp,
            reason
        )

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


def get_events(file, sec: int = 0) -> iter(List[HTCJobEvent]):

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
            reason = f"File was manipulated or contains gpu data: {file_name}"
        else:
            reason = f"Not able to open the file: {file_name}"

        raise ReadLogException(reason)


def get_condor_log(
        file: str,
        rdns_lookup=False
) -> CondorLog:
    """
    Read the log file with the htcondor module.

    Return five dicts holding information about:
    execution node, used resources, times, used ram history and errors

    :type file: str
    :param file: HTCondor log file
    :param rdns_lookup: reverse dns lookup for ip-adresses
    :return: job_details, resources, time_manager, ram_history, errors

    Consider that the return values can be None or empty dictionaries
    """
    submission_event = None
    execution_event = None
    termination_event = None
    image_size_events = []
    occurred_errors = []
    events = []
    event_handler = EventHandler()
    error_while_reading = False

    try:
        for event in get_events(file):
            events.append(event)
    except ReadLogException as err:
        logging.debug(err)
        rprint(f"[red]{err}[/red]")
        error_while_reading = True
        occurred_errors.append(
            ErrorEvent(
                None,
                None,
                JobState.ERROR_WHILE_READING,
                reason=str(err)
            )
        )

    for event in events:

        if event.type == jet.SUBMIT:
            job_event = event_handler.get_submission_event(event)
            if isinstance(job_event, JobSubmissionEvent):
                submission_event = job_event

        elif event.type == jet.EXECUTE:
            job_event = event_handler.get_execution_event(
                event,
                rdns_lookup=rdns_lookup
            )
            if isinstance(job_event, JobExecutionEvent):
                execution_event = job_event

        elif event.type == jet.IMAGE_SIZE:
            job_event = event_handler.get_image_size_event(event)
            image_size_events.append(job_event)

        # update resource dict and termination date
        elif event.type == jet.JOB_TERMINATED:
            job_event = event_handler.get_job_terminated_event(event)
            termination_event = job_event

        # update error dict and termination date
        elif event.type == jet.JOB_ABORTED:
            job_event = event_handler.get_job_aborted_event(event)

        # update error dict
        elif event.type == jet.JOB_HELD:
            job_event = event_handler.get_job_held_event(event)

        # update error dict
        elif event.type == jet.SHADOW_EXCEPTION:
            job_event = event_handler.get_shadow_exception_event(event)

        else:
            job_event = None
            rprint(
                f"[yellow]Event type: {event.type} "
                f"not handled yet[/yellow]"
            )

        if isinstance(job_event, ErrorEvent):
            occurred_errors.append(job_event)
            if isinstance(job_event, JobTerminationEvent):
                termination_event = job_event

    # End of the file

    if error_while_reading:
        event_handler.state_manager.state = JobState.ERROR_WHILE_READING

    set_events = SETEvents(
        submission_event,
        execution_event,
        termination_event,
    )
    job_details = JobDetails(
        set_events,
        event_handler.state_manager
    )
    error_events = ErrorEvents(occurred_errors)
    ram_history = RamHistory(image_size_events)

    return CondorLog(
        file,
        job_details,
        error_events,
        ram_history
    )
