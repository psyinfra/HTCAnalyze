from abc import ABC

import os
from htcanalyze.globals import BAD_USAGE, TOLERATED_USAGE


class View(ABC):

    def __init__(
            self,
            bad_usage=BAD_USAGE,
            tolerated_usage=TOLERATED_USAGE
    ):
        self.bad_usage = bad_usage
        self.tolerated_usage = tolerated_usage


def read_file(file: str):
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
        rprint(f"[yellow]There is no file: {file}")
    except TypeError as err:
        logging.exception(err)

    return output_string