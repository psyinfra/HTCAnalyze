"""Class to define HTCondor Joblog resources."""

from typing import List
from numpy import nan_to_num as ntn


class Resource:
    """
    Class of one single HTCondor-JobLog resource.

    One file contains usually multiple resources,
    so that nested lists represent a collection of job resources
    """

    level_colors = {'error': 'red', 'warning': 'yellow',
                    'light_warning': 'yellow2', 'normal': 'green'}

    def __init__(self,
                 description: str,
                 usage: float,
                 requested: float,
                 allocated: float):
        # except description, naming in __init__ arguments should be
        #   consistent with names in the resources dictionary
        self.description = description
        self.usage = usage
        self.requested = requested
        self.allocated = allocated
        self.warning_level = None

    def get_color(self) -> str:
        """Convert an alert level to an appropriate color."""
        return self.level_colors.get(self.warning_level, "default")

    def resource_to_dict(self) -> dict:
        """Return this class as a dict."""
        return {k: v for k, v in self.__dict__.items()
                if not k == "level_colors"}

    def __repr__(self):
        """Own style of representing this class."""
        return f"({self.description}, " \
            f"{self.usage}, " \
            f"{self.requested}, " \
            f"{self.allocated}, " \
            f"{self.warning_level})"

    def __str__(self):
        """Create a string representation of this class."""
        s_res = f"Resource: {self.description}\n" \
            f"Usage: [{self.get_color()}]{self.usage}[/{self.get_color()}], " \
            f"Requested: {self.requested}, " \
            f"Allocated: {self.allocated}"
        return s_res

    def chg_lvl_on_threholds(self, bad_usage, tolerated_usage):
        """Set warning level depending on thresholds."""
        if self.requested != 0:
            deviation = self.usage / self.requested

            if str(self.usage) == 'nan':
                self.warning_level = 'light_warning'
            elif not 1 - bad_usage <= deviation <= 1 + bad_usage:
                self.warning_level = 'error'
            elif not 1 - tolerated_usage <= deviation <= 1 + tolerated_usage:
                self.warning_level = 'warning'
            else:
                self.warning_level = 'normal'
        elif self.usage > 0:  # Usage without any request ? NOT GOOD
            self.warning_level = 'error'
        else:
            self.warning_level = 'normal'


def create_avg_on_resources(
        job_resource_list: List[List[Resource]]
) -> List[Resource]:
    """
    Create a new List of Resources in Average.

    :param job_resource_list: list(list(Resource))
    :return: list(Resource)
    """
    n_jobs = len(job_resource_list)
    res_cache = dict()

    # calc total
    for job_resources in job_resource_list:
        for resource in job_resources:
            desc = resource.description  # description shortcut
            # add resource
            if res_cache.get(desc):
                res_cache[desc].usage += ntn(resource.usage)
                res_cache[desc].requested += ntn(resource.requested)
                res_cache[desc].allocated += ntn(resource.allocated)
            # create first entry
            else:
                res_cache[desc] = Resource(desc,
                                           ntn(resource.usage),
                                           ntn(resource.requested),
                                           ntn(resource.allocated))

    avg_res_list = list(res_cache.values())

    # calc avg
    for resource in avg_res_list:
        resource.description = "Average " + resource.description
        resource.usage = round(resource.usage / n_jobs, 3)
        resource.requested = round(resource.requested / n_jobs, 2)
        resource.allocated = round(resource.allocated / n_jobs, 2)

    return avg_res_list


def refactor_resources(resources: dict) -> List[Resource]:
    """Convert a dict of lists to a list of Resource objects."""
    resources = {k.lower(): v for k, v in resources.items()}
    resources["description"] = resources.pop("resources")
    resources = [dict(zip(resources, v)) for v in zip(*resources.values())]
    resources = [Resource(**resource) for resource in resources]
    return resources


def convert_res_to_dict(resources: List[Resource]) -> dict:
    """Convert a list of Resource back to this dict scheme."""
    return {
        "Resources": [res.description for res in resources],
        "Usage": [f"[{res.get_color()}]{res.usage}[/{res.get_color()}]"
                  for res in resources],
        "Requested": [res.requested for res in resources],
        "Allocated": [res.allocated for res in resources]
    }
