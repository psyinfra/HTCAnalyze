
from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE
from .view import View


class ResourceView(View):

    def __init__(
            self,
            resources,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE
    ):
        super().__init__()
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
