"""Class to define HTCondor Joblog resources"""

from rich import print as rprint
from typing import List


class Resource:
    """
    Class of one single resource.

    """
    level_colors = {'error': 'red', 'warning': 'yellow',
                    'light_warning': 'yellow2', 'normal': 'green'}

    def __init__(self,
                 name: str,
                 usage: float,
                 requested: float,
                 allocated: float,
                 warning_level: str = None):
        # naming in __init__ arguments should be
        # consistent with names in the resources dictionary
        self.name = name
        self.usage = usage
        self.requested = requested
        self.allocated = allocated
        self.warning_level = warning_level

    def get_color(self) -> str:
        """Convert an alert level to an appropriate color"""
        return self.level_colors.get(self.warning_level, "")

    def resource_to_dict(self) -> dict:
        """Return this class as a dict."""
        return {k: v for k, v in self.__dict__.items()
                if not k == "level_colors"}

    def __repr__(self):
        return f"({self.name}, " \
            f"{self.usage}, " \
            f"{self.requested}, " \
            f"{self.allocated}), " \
            f"{self.warning_level}"

    def __str__(self):
        """Create a string representation of this class."""
        s_res = f"Resource: {self.name}\n" \
            f"Usage: [{self.get_color()}]{self.usage}[/{self.get_color()}], " \
            f"Requested: {self.requested}, " \
            f"Allocated: {self.allocated}"
        return s_res

    def chg_lvl_on_threholds(self, bad_usage, tolerated_usage):
        """Set warning level depending on thresholds."""
        if self.requested != 0:
            deviation = self.usage / self.requested

            if not 1 - bad_usage <= deviation <= 1 + bad_usage:
                self.warning_level = 'error'
            elif not 1 - tolerated_usage <= deviation <= 1 + tolerated_usage:
                self.warning_level = 'warning'
            elif str(self.usage) == 'nan':
                self.warning_level = 'light_warning'
            else:
                self.warning_level = 'normal'
        elif self.usage > 0:  # Usage without any request ? NOT GOOD
            self.warning_level = 'error'
        else:
            self.warning_level = 'normal'


def refactor_resources(resources: dict) -> List[Resource]:
    """Convert a dict of lists to a list of Resource objects"""
    resources = {k.lower(): v for k, v in resources.items()}
    resources["name"] = resources.pop("resources")
    resources = [dict(zip(resources, v)) for v in zip(*resources.values())]
    resources = [Resource(**resource) for resource in resources]
    return resources
