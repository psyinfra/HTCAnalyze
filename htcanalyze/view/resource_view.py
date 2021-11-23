"""Module to visualize log resources."""
from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE
from .view import View


class ResourceView(View):
    """
    Visualizes resources as a table with coloring based on thresholds
    regarding the usage and request of resources.

    If the usage of a resource is less than the requested space
    by a certain percentage, use some coloring to visualize that this is
    a bad (red) or still tolerated behaviour (yellow).

    The percentage is given as float

    :param resources: resources
    :param bad_usage: bad usage threshold in %
    :param tolerated_usage: tolerated usage threshold in %
    """

    def __init__(
            self,
            resources,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE,
            console=None
    ):
        super().__init__(console=console)
        self.resources = resources
        self.bad_usage = bad_usage
        self.tolerated_usage = tolerated_usage

    def print_resources(
            self,
            headers=None,
            precision=3
    ):
        """Prints a resource table."""
        if not self.resources:
            return

        if headers is None:
            headers = [
                "Partitionable Resources",
                "Usage",
                "Request",
                "Allocated"
            ]

        resource_table = self.create_table(headers)

        for resource in self.resources.resources:
            if not resource.is_empty():
                color = resource.get_color_by_threshold(
                    bad_usage=self.bad_usage,
                    tolerated_usage=self.tolerated_usage
                )
                resource_table.add_row(
                    resource.description,
                    f"[{color}]{round(resource.usage, precision)}[/{color}]",
                    str(round(resource.requested, precision)),
                    str(round(resource.allocated, precision))
                )

        self.console.print(resource_table)
