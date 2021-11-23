"""Manage HTCondor job log resources."""

import json
from abc import ABC
from enum import Enum
from typing import List
from numpy import isnan, nan_to_num as ntn

from htcanalyze import ReprObject


class LevelColors(Enum):
    """Coloring for different usages."""
    ERROR = 'red'
    WARNING = 'yellow'
    LIGHT_WARNING = 'yellow2'
    NORMAL = 'green'


class LogResource(ABC):
    """
    Class of one single HTCondor-JobLog resource.

    One file contains usually multiple resources,
    so that nested lists represent a collection of job resources

    :param usage:
    :param requested:
    :param allocated:
    :param description:
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
        if not isinstance(other, self.__class__) or other.is_empty():
            return self
        return self.__class__(
            float(ntn(self.usage) + ntn(other.usage)),
            float(ntn(self.requested) + ntn(other.requested)),
            float(ntn(self.allocated) + ntn(other.allocated))
        )

    def __truediv__(self, other):
        assert isinstance(other, (float, int))
        if self.is_empty():
            return self
        return self.__class__(
            float(ntn(self.usage) / other),
            float(ntn(self.requested) / other),
            float(ntn(self.allocated) / other)
        )

    def is_empty(self) -> bool:
        """Returns true if all values are NaN."""
        return (
                isnan(self.usage) and
                isnan(self.requested) and
                isnan(self.allocated)
        )

    def __radd__(self, other):
        if not isinstance(other, self.__class__) or other.is_empty():
            return self
        return self + other

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
        """Get coloring depending on thresholds."""
        warning_level = self.get_warning_lvl_by_threshold(
            bad_usage,
            tolerated_usage
        )
        return self.get_color(warning_level)

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        usage_equal = (
                self.usage == other.usage or
                (isnan(self.usage) and isnan(other.usage))
        )
        requested_equal = (
                self.requested == other.requested or
                (isnan(self.requested) and isnan(other.requested))
        )
        allocated_equal = (
                self.allocated == other.allocated or
                (isnan(self.allocated) and isnan(other.allocated))
        )
        return usage_equal and requested_equal and allocated_equal


class CPULogResource(LogResource):
    """Represents a CPU log resource."""

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super().__init__(usage, requested, allocated, "Cpus")


class DiskLogResource(LogResource):
    """Represents a disk log resource."""

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super().__init__(usage, requested, allocated, "Disk (KB)")


class MemoryLogResource(LogResource):
    """Represents a memory log resource."""

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float
    ):
        super().__init__(usage, requested, allocated, "Memory (MB)")


class GPULogResource(LogResource):
    """Represents a GPU log resource."""

    def __init__(
            self,
            usage: float,
            requested: float,
            allocated: float,
            assigned: str = ""
    ):
        super().__init__(usage, requested, allocated, "Gpus (Average)")
        self.assigned = assigned


class LogResources(ReprObject):
    """
    Represents log resources of a single log file.

    :param cpu_resource:
    :param disc_resource:
    :param memory_resource:
    :param gpu_resource: Optional
    """
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
    def resources(self) -> List[LogResource]:
        """Returns resource list."""
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
        return self if not isinstance(other, self.__class__) else self + other

    def __eq__(self, other):
        return (
            self.cpu_resource == other.cpu_resource and
            self.disc_resource == other.disc_resource and
            self.memory_resource == other.memory_resource and
            self.gpu_resource == other.gpu_resource
        )
