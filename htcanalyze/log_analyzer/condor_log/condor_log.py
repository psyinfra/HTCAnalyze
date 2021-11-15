import os
import json

from htcanalyze import ReprObject
from .job_details import JobDetails
from .error_events import LogfileErrorEvents
from .ram_history import RamHistory


class CondorLog(ReprObject):

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
        return self.job_details.resources
