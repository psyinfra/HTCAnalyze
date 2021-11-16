"""Module for a basic abstract view class."""
import os
import logging

from typing import List
from abc import ABC

from rich.console import Console
from rich.table import Table, box
from rich.text import Text
from rich.progress import Progress

from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE


def track_progress(
        generator,
        n_items=100,
        tracking_title="...",
):
    """
    Visualize the process of generating objects.
    Takes a generator and generates a finite amount of objects.

    :param generator: generator or iterrator
    :param n_items: if possible provide the number of objects
    :param tracking_title: Title of the process
    :return:
    """
    with Progress(
            transient=True,
            redirect_stdout=False,
            redirect_stderr=False,
            expand=True
    ) as progress:
        task = progress.add_task(tracking_title, total=n_items)
        items = []
        for item in generator:
            progress.update(task, advance=1)
            items.append(item)
        return items


class View(ABC):
    """A general view to visualize HTCAnalyze data to the terminal.

    :param bad_usage: bad usage threshold
    :param tolerated_usage: tolerated usage threshold
    """

    def __init__(self):
        self.console = Console()
        self.window_width = self.console.size.width

    def read_file(self, file: str):
        """
        Read a file.

        :param: file
        :return: content
        """
        output_string = None
        try:

            if os.path.getsize(file) == 0:
                return ""

            with open(file, "r", encoding='utf-8') as output_content:
                output_string = output_content.read()
        except NameError as err:
            logging.exception(err)
        except FileNotFoundError:
            self.console.print(f"[yellow]There is no file: {file}")
        except TypeError as err:
            logging.exception(err)

        return output_string

    @staticmethod
    def create_table(headers: List, title=None) -> Table:
        """Creates a rich table."""
        return Table(
            *headers,
            title=title,
            expand=True,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )

    def print_desc_line(
            self,
            desc_str,
            desc_value,
            color="default",
            highlight_char="#",
            boxing=False
    ):
        """
        Prints a description line with the length of the terminal.
        The title should be less than the width of the terminal, the
        rest of the space is filled with hightlight_char to fill the gaps.
        The desc_str is centered.

        :param self:
        :param desc_str: raw desc
        :param desc_value: a value that is colored
        :param color: coloring of the desc_value
        :param highlight_char: character to fill the rest of the line
        :param boxing: adds one line above and below the desc line
        :return:
        """
        with_color = f"{desc_str} [{color}]{desc_value}[/{color}]"
        raw_text = Text.from_markup(with_color)

        fill_up_len = int((self.window_width - len(raw_text)) / 2)
        fill_up_str = highlight_char*fill_up_len
        full_state_str = f"{fill_up_str} {raw_text} {fill_up_str}"
        overhang = len(full_state_str) - self.window_width
        fill_up_str2 = fill_up_str[:-overhang]

        if boxing:
            print(highlight_char*self.window_width)

        self.console.print(f"{fill_up_str} {with_color} {fill_up_str2}")

        if boxing:
            print(highlight_char*self.window_width)
