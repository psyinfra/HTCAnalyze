"""Class to define HTCondor Joblog resources."""

import json
import math
from typing import List
from numpy import nan_to_num as ntn

LEVEL_COLORS = {
    'error': 'red',
    'warning': 'yellow',
    'light_warning': 'yellow2',
    'normal': 'green'
}


class LogResource:
    """
    Class of one single HTCondor-JobLog resource.

    One file contains usually multiple resources,
    so that nested lists represent a collection of job resources

    """

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float,
            description: str = None,
    ):
        self.usage = usage
        self.requested = requested
        self.allocated = allocated
        self.description = description

    def __add__(self, other):
        if other == 0:
            return self
        assert type(self) == type(other)
        return self.__class__(
            float(ntn(self.usage) + ntn(other.usage)),
            float(ntn(self.requested) + ntn(other.requested)),
            float(ntn(self.allocated) + ntn(other.allocated))
        )

    def __truediv__(self, other):
        return self.__class__(
            float(ntn(self.usage) / other),
            float(ntn(self.requested) / other),
            float(ntn(self.allocated) / other)
        )

    def is_empty(self):
        return (
                math.isnan(self.usage) and
                math.isnan(self.requested) and
                math.isnan(self.allocated)
        )

    def __radd__(self, other):
        return self if other == 0 or other.is_empty() else self + other

    def to_dict(self) -> dict:
        """Return this class as a dict."""
        return {k: v for k, v in self.__dict__.items()
                if not k == "level_colors"}

    def __repr__(self):
        """Own style of representing this class."""
        return json.dumps(self.__dict__)

    def __str__(self):
        """Create a string representation of this class."""
        s_res = f"LogResource: {self.description}\n" \
            f"Usage: [{self.get_color()}]{self.usage}[/{self.get_color()}], " \
            f"Requested: {self.requested}, " \
            f"Allocated: {self.allocated}"
        return s_res

    @staticmethod
    def get_color(warning_level) -> str:
        """Convert an alert level to an appropriate color."""
        return LEVEL_COLORS.get(warning_level, "default")

    def get_color_by_threshold(self, bad_usage, tolerated_usage):
        """Set warning level depending on thresholds."""
        if self.requested != 0:
            deviation = self.usage / self.requested

            if str(self.usage) == 'nan':
                warning_level = 'light_warning'
            elif not 1 - bad_usage <= deviation <= 1 + bad_usage:
                warning_level = 'error'
            elif not 1 - tolerated_usage <= deviation <= 1 + tolerated_usage:
                warning_level = 'warning'
            else:
                warning_level = 'normal'
        elif self.usage > 0:  # Usage without any request ? NOT GOOD
            warning_level = 'error'
        else:
            warning_level = 'normal'

        return self.get_color(warning_level)


class CPULogResource(LogResource):
    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super(CPULogResource, self).__init__(
            usage, requested, allocated, "Cpus"
        )


class DiskLogResource(LogResource):
    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super(DiskLogResource, self).__init__(
            usage, requested, allocated, "Disk (KB)"
        )


class MemoryLogResource(LogResource):
    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super(MemoryLogResource, self).__init__(
            usage, requested, allocated, "Memory (MB)"
        )


class GPULogResource(LogResource):

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float,
            assigned: str = ""
    ):
        super(GPULogResource, self).__init__(
            usage, requested, allocated, "Gpus (Average)"
        )
        self.assigned = assigned


class LogResources:
    def __init__(
            self,
            cpu_resource: CPULogResource,
            disc_resource: DiskLogResource,
            memory_resource: MemoryLogResource,
            gpu_resource: GPULogResource = None
    ):
        self.cpu_resource = cpu_resource
        self.disc_resource = disc_resource
        self.memory_resource = memory_resource
        self.gpu_resource = gpu_resource

    @property
    def resources(self):
        return [
            self.cpu_resource,
            self.disc_resource,
            self.memory_resource,
            self.gpu_resource
        ]

    def __add__(self, other):
        return LogResources(
            self.cpu_resource + other.cpu_resource,
            self.disc_resource + other.disc_resource,
            self.memory_resource + other.memory_resource,
            self.gpu_resource + other.gpu_resource
        )

    def __truediv__(self, other):
        return LogResources(
            self.cpu_resource / other,
            self.disc_resource / other,
            self.memory_resource / other,
            self.gpu_resource / other
        )

    def __radd__(self, other):
        return self if other == 0 else self + other

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )


def create_avg_on_resources(
        log_resource_list: List[LogResources]
) -> List[LogResource]:
    """
    Create a new List of Resources in Average.

    :param log_resource_list: list(list(LogResource))
    :return: list(LogResource)
    """
    n_jobs = len(log_resource_list)
    res_cache = {}

    # calc total
    for log_resources in log_resource_list:
        for resource in log_resources.resources:
            desc = resource.description  # description shortcut
            # add resource
            if res_cache.get(desc):
                res_cache[desc].usage += ntn(resource.usage)
                res_cache[desc].requested += ntn(resource.requested)
                res_cache[desc].allocated += ntn(resource.allocated)
            # create first entry
            else:
                res_cache[desc] = LogResource(
                    desc,
                    ntn(resource.usage),
                    ntn(resource.requested),
                    ntn(resource.allocated)
                )

    avg_res_list = list(res_cache.values())

    # calc avg
    for resource in avg_res_list:
        resource.description = "Average " + resource.description
        resource.usage = round(resource.usage / n_jobs, 3)
        resource.requested = round(resource.requested / n_jobs, 2)
        resource.allocated = round(resource.allocated / n_jobs, 2)

    return avg_res_list


def dict_to_resources(resources: dict) -> List[LogResource]:
    """Convert a dict of lists to a list of LogResource objects."""
    resources = {k.lower(): v for k, v in resources.items()}
    resources["description"] = resources.pop("resources")
    resources = [dict(zip(resources, v)) for v in zip(*resources.values())]
    resources = [LogResource(**resource) for resource in resources]
    return resources


def resources_to_dict(resources: List[LogResource]) -> dict:
    """Convert a list of LogResource back to this dict scheme."""
    if resources:
        return {
            "Resources": [res.description for res in resources],
            "Usage": [f"[{res.get_color()}]{res.usage}[/{res.get_color()}]"
                      for res in resources],
            "Requested": [res.requested for res in resources],
            "Allocated": [res.allocated for res in resources]
        }
    # else:
    return {}
