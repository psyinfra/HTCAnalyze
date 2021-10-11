
import os
import logging
from abc import ABC

from rich.console import Console
from rich.table import Table, box

from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE


class View(ABC):

    def __init__(
            self,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE
    ):
        self.console = Console()
        self.window_width = self.console.size.width
        self.bad_usage = bad_usage
        self.tolerated_usage = tolerated_usage

    def print_resources(
            self,
            resources,
            title="Job Resources",
            precision=3
    ):
        if not resources:
            return

        resource_table = Table(
            *["Partitionable Resources", "Usage ", "Request", "Allocated"],
            width=self.window_width,
            title=title,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )

        for resource in resources.resources:
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

    def read_file(self, file: str):
        """
        Read a file.

        :param: file
        :return: content
        """
        output_string = ""
        try:

            if os.path.getsize(file) == 0:
                return output_string

            with open(file, "r", encoding='utf-8') as output_content:
                output_string = output_content.read()
        except NameError as err:
            logging.exception(err)
        except FileNotFoundError:
            self.consol.print(f"[yellow]There is no file: {file}")
        except TypeError as err:
            logging.exception(err)

        return output_string
