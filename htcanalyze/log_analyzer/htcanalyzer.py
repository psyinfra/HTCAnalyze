"""module to summarize and analyze HTCondor log files."""

import logging
from typing import List
from rich import print as rprint

# import own module
from .condor_log import CondorLog, ErrorEvents, RamHistory
from .event_handler import EventHandler, ReadLogException, ErrorEvent, \
    SETEvents, JobExecutionEvent, JobSubmissionEvent, \
    JobTerminationEvent, ImageSizeEvent
from .event_handler.states import JobState, ErrorState
from .condor_log import JobDetails


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
            rdns_lookup=False
    ):
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

    @staticmethod
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
        condor_event_handler = EventHandler()

        try:
            for event in condor_event_handler.get_events(file):

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

                if job_event is None:
                    rprint(
                        f"[yellow]Event type: {event.type} "
                        f"not handled yet[/yellow]"
                    )

        except ReadLogException as err:
            logging.debug(err)
            rprint(f"[red]{err}[/red]")
            occurred_errors.append(
                ErrorEvent(
                    None,
                    None,
                    ErrorState.ERROR_WHILE_READING,
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
        error_events = ErrorEvents(occurred_errors)
        ram_history = RamHistory(image_size_events)

        return CondorLog(
            file,
            job_details,
            error_events,
            ram_history
        )
