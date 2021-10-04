import logging
import re

from typing import List
from datetime import datetime as date_time
from htcondor import JobEventLog, JobEventType as jet
from rich import print as rprint
import numpy as np

from .job_details import JobDetails
from .resource import Resource
from .time_manager import TimeManager
from .state_manager import StateManager
from .ram_history import RamHistory
from .events import *


def event_decorator(func):
    def wrapper(self, event, *args, **kwargs):
        self._event_number = event.get('EventTypeNumber')
        self._time_stamp = date_time.strptime(
            event.get('EventTime'),
            "%Y-%m-%dT%H:%M:%S"
        )
        return func(self, event, *args, **kwargs)

    return wrapper


class CondorLog:

    _state = None

    class State(Enum):
        WAITING = 0
        RUNNING = 1
        TERMINATED = 2
        ERROR = 3

    def __init__(
            self,
            job_details: JobDetails,
            resources: List[Resource],
            time_manager: TimeManager,
            errors: List[ErrorEvent],
            ram_history: RamHistory
    ):
        self.job_details = job_details
        self.resources = resources
        self.time_manager = time_manager
        self.errors = errors
        self.ram_history = ram_history
        self._state = self._get_state()

    def _get_state(self) -> State:
        if self.time_manager.termination_date:
            return CondorLog.State.TERMINATED
        elif self.time_manager.execution_date:
            return CondorLog.State.RUNNING
        elif self.time_manager.submission_date:
            return CondorLog.State.WAITING
        else:
            return CondorLog.State.ERROR

    def get_state_color(self):
        """Return the color for the given state."""
        return self.state_colors.get(self.state)

    @property
    def state(self):
        return self._state

    @state.setter
    def __setstate__(self, state):
        self._state = state


class CondorEventHandler:
    _event_number = None
    _time_stamp = None

    def __init__(self):
        self.state_manager = StateManager()

    @event_decorator
    def get_submission_event(
            self,
            event
    ) -> JobEvent:
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
        error_code = "INVALID_USER_ADDRESS"
        self.state_manager.state = JobState.ERROR_WHILE_READING
        return ErrorEvent(
            self._event_number,
            None,
            error_code,
            reason
        )

    @event_decorator
    def get_execution_event(
            self,
            event,
            rdns_lookup=False
    ) -> JobEvent:
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
            error_code = "INVALID_HOST_ADDRESS"
            self.state_manager.state = JobState.ERROR_WHILE_READING
            return ErrorEvent(
                self._event_number,
                None,
                error_code,
                reason
            )

    @event_decorator
    def get_job_terminated_event(
            self,
            event
    ):

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
                "CPU",
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
        # mostly due to signal/exit code 11
        else:
            state = JobState.ABNORMAL_TERMINATION
            return_value = event.get('TerminatedBySignal')

        self.state_manager.state = state
        return JobTerminationEvent(
            self._event_number,
            self._time_stamp,
            resources,
            state,
            return_value
        )

    @event_decorator
    def get_job_aborted_event(
            self,
            event
    ) -> JobEvent:
        assert event.type == jet.JOB_ABORTED
        reason = event.get('Reason')
        self.state_manager.state = JobState.ABORTED
        return JobAbortedEvent(
            self._event_number,
            self._time_stamp.date.strftime("%m/%d %H:%M:%S"),
            reason
        )

    @event_decorator
    def get_image_size_event(
            self,
            event
    ) -> JobEvent:
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
    def get_job_held_event(
            self,
            event
    ) -> JobEvent:
        assert event.type == jet.JOB_HELD
        reason = event.get('HoldReason')
        return JobHeldEvent(
            self._event_number,
            self._time_stamp.strftime("%m/%d %H:%M:%S"),
            reason
        )

    @event_decorator
    def get_shadow_exception_event(
            self,
            event
    ) -> JobEvent:
        assert event.type == jet.SHADOW_EXCEPTION
        reason = event.get('Message')
        return ShadowExceptionEvent(
            self._event_number,
            self._time_stamp.strftime("%m/%d %H:%M:%S"),
            reason
        )

    def get_events(self, file, sec: int = 0) -> List[JobEventLog]:

        jel = JobEventLog(file)
        events = []

        try:
            # Read all currently-available events
            # waiting for 'sec' seconds for the next event.
            for event in jel.events(sec):
                events.append(event)

        except OSError as err:
            logging.exception(err)
            if err.args[0] == "ULOG_RD_ERROR":
                reason = (
                    "Error while reading log file. "
                    "File was manipulated or contains gpu usage."
                )

            else:
                reason = f"Not able to open the file: {file}"
            raise ReadLogException(reason)

        return events

    def get_condor_log(
            self,
            file: str,
            rdns_lookup=False
    ) -> CondorLog:
        """
        Read the log file with the htcondor module.

        Return five dicts holding information about:
        execution node, used resources, times, used ram history and errors

        :type file: str
        :param file: HTCondor log file
        :param sec: seconds to wait for new events
        :return: job_details, resources, time_manager, ram_history, errors

        Consider that the return values can be None or empty dictionaries
        """
        resources = []
        submission_event = None
        execution_event = None
        termination_event = None
        image_size_events = []
        occurred_errors = []

        try:
            events = self.get_events(file)
        except ReadLogException as err:
            logging.debug(err)
            rprint()

        job_events = []

        for event in events:

            if event.type == jet.SUBMIT:
                job_event = self.get_submission_event(event)
                if isinstance(job_event, JobSubmissionEvent):
                    submission_event = job_event

            elif event.type == jet.EXECUTE:
                job_event = self.get_execution_event(
                    event,
                    rdns_lookup=rdns_lookup
                )
                if isinstance(job_event, JobExecutionEvent):
                    execution_event = job_event

            elif event.type == jet.IMAGE_SIZE:
                job_event = self.get_image_size_event(event)
                image_size_events.append(job_event)

            # update resource dict and termination date
            elif event.type == jet.JOB_TERMINATED:
                job_event = self.get_job_terminated_event(event)
                termination_event = job_event

            # update error dict and termination date
            elif event.type == jet.JOB_ABORTED:
                job_event = self.get_job_aborted_event(event)
                termination_event = job_event
                occurred_errors.append(job_event)

            # update error dict
            elif event.type == jet.JOB_HELD:
                job_event = self.get_job_held_event(event)
                occurred_errors.append(job_event)

            # update error dict
            elif event.type == jet.SHADOW_EXCEPTION:
                job_event = self.get_shadow_exception_event(event)
                occurred_errors.append(job_event)

            else:
                job_event = None
                rprint(
                    f"[yellow]Event type: {event.type} "
                    f"not handled yet[/yellow]"
                )

            if isinstance(job_event, ErrorEvent):
                if job_event.is_termination_event:
                    termination_event = job_event
                rprint(
                    f"[red]{job_event.error_name}: {job_event.reason}[/red]"
                )

            job_events.append(job_event)

        # End of the file

        time_manager = TimeManager(
            submission_event,
            execution_event,
            termination_event
        )

        job_details = JobDetails(
            submission_event,
            execution_event,
            termination_event
        )

        ram_history = RamHistory(image_size_events)

        return CondorLog(
            job_details,
            resources,
            time_manager,
            occurred_errors,
            ram_history
        )
