"""HTCondor job log validator."""

import os
import re
import logging
from typing import List

from rich import print as rprint
from htcanalyze.globals import (
    EXT_LOG_DEFAULT,
    EXT_OUT_DEFAULT,
    EXT_ERR_DEFAULT
)


class LogValidator:
    """
    HTCondor LogValidator.

    :param ext_log: log file extension (default: .log)
    :param ext_err: stderr file extension (default: .err)
    :param ext_out: stdout file extension (default: .out)
    """

    def __init__(
            self,
            ext_log=EXT_LOG_DEFAULT,
            ext_err=EXT_ERR_DEFAULT,
            ext_out=EXT_OUT_DEFAULT
    ):
        self.ext_log = ext_log
        self.ext_err = ext_err
        self.ext_out = ext_out

    def is_valid_logfile(self, file) -> bool:
        """
        Validate a single HTCondor log file using regex.

        :param file: HTCondor log file
        :return: True when valid else False
        """
        # if not ending with ext_log
        if self.ext_log.__ne__("") and not file.endswith(self.ext_log):
            return False

        # does also not end with ext_err and ext_out suffix
        if self.ext_err.__ne__("") and file.endswith(self.ext_err):
            return False
        if self.ext_out.__ne__("") and file.endswith(self.ext_out):
            return False

        if os.path.getsize(file) == 0:  # file is empty
            logging.debug("%s is empty", file)
            return False

        try:
            with open(file, "r", encoding='utf-8') as read_file:
                return bool(
                    re.match(
                        r"[0-9]{3} \([0-9]+.[0-9]+.[0-9]{3}\)",
                        read_file.readline()
                    )
                )
        except (FileNotFoundError, TypeError):
            return False

    def validate_dir(
            self,
            directory,
            recursive=False
    ) -> List[str]:
        """
        Validate all files inside the given directory.

        :param directory: path to directory with logs
        :param recursive: Search recursively for log files
        :return:
        """

        walk_dir = os.walk(directory, topdown=True)
        if recursive:
            for root, dirs, files in walk_dir:
                if not dirs:
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.is_valid_logfile(file_path):
                            yield file_path
        else:
            root, _, files = next(walk_dir)
            for file in files:
                file_path = os.path.join(root, file)
                if self.is_valid_logfile(file_path):
                    yield os.path.join(root, file)

    def common_validation(self, path_list, recursive=False):
        """
        Filters paths for valid HTCondor log files

        :param path_list: list of HTCondor log paths
        :param recursive: Search recursively for log files
        :return: list with valid HTCondor log files
        """
        valid_files = []

        for arg in path_list:

            abs_path = os.path.abspath(arg)
            if os.path.isdir(abs_path):
                for file_path in self.validate_dir(abs_path, recursive):
                    yield file_path
            elif (
                    os.path.isfile(abs_path) or
                    os.path.isfile(abs_path + self.ext_log)
            ):
                # check if valid file or try to resolve with the extension,
                # if only id was given
                if self.is_valid_logfile(abs_path):
                    yield abs_path
                else:
                    rprint(
                        f"[yellow]The given file {abs_path} "
                        f"is not a valid HTCondor log file[/yellow]"
                    )
            else:
                rprint(f"[red]The given path: {arg} does not exist[/red]")

        return valid_files
