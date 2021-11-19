"""module to summarize and analyze HTCondor log files."""

import logging
import os.path
from typing import List
from rich.console import Console

# import own module
from .condor_log.condor_log import (
    CondorLog,
    LogfileErrorEvents,
    RamHistory,
    JobDetails
)
from .event_handler.event_handler import (
    EventHandler, ReadLogException, ErrorEvent,
    JobExecutionEvent, JobSubmissionEvent,
    JobTerminationEvent, ImageSizeEvent
)
from .event_handler.set_events import SETEvents
from .event_handler.states import ErrorWhileReadingState


class HTCAnalyzer:
    """
    This class is able to analyze HTCondor Joblogs.

    The modes:
        analyze,
        summarize,
        analyzed-summary

    """

    def __init__(
            self,
            console=None,
            rdns_lookup=False
    ):
        self.console = console if console else Console()
        self.rdns_cache = {}
        self.rdns_lookup = rdns_lookup

    def analyze(self, log_files: List[str]) -> List[CondorLog]:
        """
        Analyze the given log files one by one.

        :param log_files: list of valid HTCondor log files
        :return: list with information of each log file
        """

        if not log_files:
            raise ValueError("No files to analyze")

        for file in log_files:
            condor_log = self.get_condor_log(file, self.rdns_lookup)
            yield condor_log

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
        :param rdns_lookup: reverse dns lookup for ip-adresses
        :return: job_details, resources, time_manager, ram_history, errors

        Consider that the return values can be None or empty dictionaries
        """
        submission_event = None
        execution_event = None
        termination_event = None
        image_size_events = []
        occurred_errors = []
        condor_event_handler = EventHandler()

        try:
            for event in condor_event_handler.get_htc_events(file):

                try:
                    job_event = condor_event_handler.get_job_event(
                        event,
                        rdns_lookup
                    )

                    if isinstance(job_event, JobSubmissionEvent):
                        submission_event = job_event

                    if isinstance(job_event, JobExecutionEvent):
                        execution_event = job_event

                    if isinstance(job_event, JobTerminationEvent):
                        termination_event = job_event

                    if isinstance(job_event, ImageSizeEvent):
                        image_size_events.append(job_event)

                    if isinstance(job_event, ErrorEvent):
                        occurred_errors.append(job_event)

                except AttributeError as err:
                    self.console.print(f"[yellow]{err}[/yellow]")

        except ReadLogException as err:
            logging.debug(err)
            self.console.print(f"[red]{err}[/red]")
            occurred_errors.append(
                ErrorEvent(
                    None,
                    None,
                    ErrorWhileReadingState(),
                    reason=str(err)
                )
            )

        # End of the file

        set_events = SETEvents(
            submission_event,
            execution_event,
            termination_event,
        )
        job_details = JobDetails(
            set_events,
            condor_event_handler.state
        )
        error_events = LogfileErrorEvents(
            occurred_errors,
            os.path.basename(file)
        )
        ram_history = RamHistory(image_size_events)

        return CondorLog(
            file,
            job_details,
            error_events,
            ram_history
        )
