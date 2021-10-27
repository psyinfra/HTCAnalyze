"""HTCondor job log validator."""

import os
import re
import logging
from typing import List

from rich import print as rprint


class LogValidator:
    """
    Create a HTCondor Joblog Validator.

    Validation is visual represented by rich.progress

    The way files are validated is by regex,
    because the htcondor module takes too much time.
    """

    def __init__(
            self,
            ext_log="",
            ext_err=".err",
            ext_out=".out"
    ):
        """Initialize."""
        self.ext_log = ext_log
        self.ext_err = ext_err
        self.ext_out = ext_out

    def is_valid_logfile(self, file) -> bool:
        """
        Validate a single HTCondor log file.

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
            logging.debug(f"{file} is empty")
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

        # print(valid_dir_files)
        #
        # # progress bar given
        # if progress_details is not None:
        #     progress = progress_details[0]
        #     task = progress_details[1]
        #     total = progress_details[2] + len(file_dir) - 1  # minus dir
        #     advance = progress_details[3]
        #     progress.console.print(
        #         f"[light_coral]Search: {directory} "
        #         f"for valid log files[/light_coral]"
        #     )
        # for file in file_dir:
        #     if progress_details is not None:
        #         progress.update(task, total=total, advance=advance)
        #
        #     # ignore hidden files or python modules
        #     if file.startswith(".") or file.startswith("__"):
        #         continue
        #
        #     # if ext_log is set, ignore other log files
        #     if self.ext_log.__ne__("") and not file.endswith(self.ext_log):
        #         logging.debug(f"Ignoring this file, {file}, "
        #                       f"because ext-log is: {self.ext_log}")
        #         continue
        #
        #     # separator handling
        #     if directory.endswith(os.path.sep):
        #         file_path = directory + file
        #     else:
        #         file_path = directory + os.path.sep + file
        #
        #     if os.path.isfile(file_path):
        #         if self.is_valid_logfile(file_path):
        #             valid_dir_files.append(file_path)
        #
        #     elif self.recursive:
        #         # total = total -1
        #         # extend files by searching through this directory
        #         valid_dir_files.extend(
        #             self.validate_dir(file_path, progress_details))
        #     else:
        #         logging.debug(f"Found subfolder: {file_path}, "
        #                       f"it will be ignored")
        #
        # return valid_dir_files

    def common_validation(self, file_list, recursive=False):
        """
        Function designed especially for this script.

        Filters given files for valid HTCondor log files,
        the process will be visual presented by rich.progress

        :param file_list: list of HTCondor logs, that need to be validated
        :param recursive: Search recursively for log files
        :return: list with valid HTCondor log files
        """
        valid_files = []

        logging.info('Validate given log files')
        for arg in file_list:

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
                logging.error(f"The given path: {arg} does not exist")
                rprint(f"[red]The given path: {arg} does not exist[/red]")

        return valid_files
