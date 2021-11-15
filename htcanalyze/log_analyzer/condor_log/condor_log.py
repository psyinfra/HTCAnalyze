"""Module to represent a log file as an CondorLog object."""

import os

from htcanalyze import ReprObject
from .job_details import JobDetails
from .error_events import LogfileErrorEvents
from .ram_history import RamHistory


class CondorLog(ReprObject):
    """
    Represents the analysis of one single log file.

    :param file: HTCondor log file
    :param job_details: JobDetails
        details about resources, times and the current state
    :param logfile_error_events: LogfileErrorEvents
        All Error Events that occurred in the log file
    :param ram_history: RamHistory
        Can be used to generate a ram histogram
    """

    def __init__(
            self,
            file: str,
            job_details: JobDetails,
            logfile_error_events: LogfileErrorEvents,
            ram_history: RamHistory
    ):
        self.file = file
        self.job_spec_id = self.get_job_spec_id(file)
        self.job_details = job_details
        self.logfile_error_events = logfile_error_events
        self.ram_history = ram_history

    @staticmethod
    def get_job_spec_id(file: str) -> str:
        """Get job specification id from a HTCondor file."""
        base = os.path.basename(file)
        return os.path.splitext(base)[0]

    @property
    def resources(self):
        """Returns log resources."""
        return self.job_details.resources
