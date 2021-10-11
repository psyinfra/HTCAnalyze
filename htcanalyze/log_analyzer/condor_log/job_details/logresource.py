"""Class to define HTCondor Joblog resources."""

import json
import math
from enum import Enum
from numpy import nan_to_num as ntn


class LevelColors(Enum):
    ERROR = 'red'
    WARNING = 'yellow'
    LIGHT_WARNING = 'yellow2'
    NORMAL = 'green'


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

    def __repr__(self):
        """Own style of representing this class."""
        return json.dumps(self.__dict__)

    @staticmethod
    def get_color(warning_level: LevelColors) -> str:
        """Get color by warning level."""
        return warning_level.value

    def get_warning_lvl_by_threshold(self, bad_usage, tolerated_usage):
        """Set warning level depending on thresholds."""
        if self.requested != 0:
            deviation = self.usage / self.requested

            if str(self.usage) == 'nan':
                warning_level = LevelColors.LIGHT_WARNING
            elif not 1 - bad_usage <= deviation <= 1 + bad_usage:
                warning_level = LevelColors.ERROR
            elif not 1 - tolerated_usage <= deviation <= 1 + tolerated_usage:
                warning_level = LevelColors.WARNING
            else:
                warning_level = LevelColors.NORMAL
        elif self.usage > 0:  # Usage without any request ? NOT GOOD
            warning_level = LevelColors.ERROR
        else:
            warning_level = LevelColors.NORMAL

        return warning_level

    def get_color_by_threshold(self, bad_usage, tolerated_usage):

        warning_level = self.get_warning_lvl_by_threshold(
            bad_usage,
            tolerated_usage
        )
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
