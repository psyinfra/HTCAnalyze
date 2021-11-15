
import json

from plotille import Figure
from htcanalyze import ReprObject
from ..event_handler.job_events import ImageSizeEvent


def _int_formatter(val, chars, delta, left=False):
    """
    Format float to int.

    Usage of this is shown here:
    https://github.com/tammoippen/plotille/issues/11
    """
    align = '<' if left else ''
    return '{:{}{}d}'.format(int(val), align, chars)


class RamHistory(ReprObject):
    """
    Create a RAM Histogram if at least two ImageSizeEvents are passed

    def __init__(self, image_size_events):
        self.image_size_events = image_size_events

    def plot_ram(self, show_legend=False) -> str:
        ram = [ram.size_update for ram in self.image_size_events]
        dates = [ram.time_stamp for ram in self.image_size_events]
        if len(ram) == 0:
            return ""  # No memory usage detected

        elif len(ram) == 1:
            return (
                f"Single memory update found:\n"
                f"Memory usage on the {dates[0]} "
                f"was updatet to {ram[0]} MB\n"
            )
        elif len(ram) > 1:

            fig = Figure()
            fig.width = 55
            fig.height = 15
            fig.set_x_limits(min_=min(dates))
            min_ram = int(min(ram))  # raises error if not casted
            fig.set_y_limits(min_=min_ram)
            fig.y_label = "Usage"
            fig.x_label = "Time"

            # this will use the self written function _
            # num_formatter, to convert the y-label to int values
            fig.register_label_formatter(float, _int_formatter)
            fig.plot(dates, ram, lc='green', label="Continuous Graph")
            fig.scatter(dates, ram, lc='red', label="Single Values")

            return fig.show(legend=show_legend)
