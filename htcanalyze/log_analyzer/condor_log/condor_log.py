import os
import json

from .job_details.job_details import JobDetails
from .error_events import ErrorEvents
from .ram_history import RamHistory


class CondorLog:

    def __init__(
            self,
            file: str,
            job_details: JobDetails,
            error_events: ErrorEvents,
            ram_history: RamHistory
    ):
        self.file = file
        self.job_spec_id = self.get_job_spec_id(file)
        self.job_details = job_details
        self.error_events = error_events
        self.ram_history = ram_history

    @staticmethod
    def get_job_spec_id(file: str) -> str:
        """Get job specification id from a HTCondor file."""
        base = os.path.basename(file)
        return os.path.splitext(base)[0]

    @property
    def resources(self):
        return self.job_details.resources

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
