import os
import json

from .job_details.job_details import JobDetails
from .resource import LogResources
from .error_events import ErrorEvents
from .ram_history import RamHistory


class CondorLog:

    def __init__(
            self,
            file: str,
            job_details: JobDetails,
            resources: LogResources,
            errors: ErrorEvents,
            ram_history: RamHistory
    ):
        self.file = file
        self.job_spec_id = self.get_job_spec_id(file)
        self.job_details = job_details
        self.resources = resources
        self.errors = errors
        self.ram_history = ram_history

    @staticmethod
    def get_job_spec_id(file: str) -> str:
        """Get job specification id from a HTCondor file."""
        base = os.path.basename(file)
        return os.path.splitext(base)[0]

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )
