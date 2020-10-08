"""HTCondor job log validator."""

import logging
import os
import re
from rich import print as rprint
from rich.progress import Progress


class LogValidator:
    """
    Create a HTCondor Joblog Validator.

    Validation is visual represented by rich.progress

    The way files are validated is by regex,
    because the htcondor module takes too much time.
    """

    def __init__(self,
                 std_log="",
                 std_err=".err",
                 std_out=".out",
                 recursive=False):
        """Initialize."""
        self.std_log = std_log
        self.std_err = std_err
        self.std_out = std_out
        self.recursive = recursive

    def validate_file(self, file) -> bool:
        """
        Validate a single HTCondor joblog file.

        :param file: HTCondor log file
        :return: True when valid else False
        """
        # if not ending with stdout
        if self.std_log.__ne__("") and not file.endswith(self.std_log):
            return False

        # does also not end with sterr and stdout suffix
        if self.std_err.__ne__("") and file.endswith(self.std_err):
            return False
        if self.std_out.__ne__("") and file.endswith(self.std_out):
            return False

        if os.path.getsize(file) == 0:  # file is empty
            logging.debug(f"{file} is empty")
            return False

        try:
            with open(file, "r") as read_file:

                if re.match(r"[0-9]{3} \([0-9]+.[0-9]+.[0-9]{3}\)",
                            read_file.readline()):

                    return True
                else:
                    return False
        except Exception:
            return False

    def validate_dir(self, directory, progress_details=None):
        """
        Validate all files inside the given directory.

        :param directory: path to directory with logs
        :param progress_details: Quadrupel (progress, task, total, advance)
        :return:
        """
        valid_dir_files = list()
        file_dir = os.listdir(directory)
        # progress bar given
        if progress_details is not None:
            progress = progress_details[0]
            task = progress_details[1]
            total = progress_details[2] + len(file_dir) - 1  # minus dir
            advance = progress_details[3]
            progress.console.print(
                f"[light_coral]Search: {directory} "
                f"for valid log files[/light_coral]")
        for file in file_dir:
            if progress_details is not None:
                progress.update(task, total=total, advance=advance)

            # ignore hidden files or python modules
            if file.startswith(".") or file.startswith("__"):
                continue

            # if std_log is set, ignore other log files
            if self.std_log.__ne__("") and not file.endswith(self.std_log):
                logging.debug("Ignoring this file, " + file +
                              ", because std-log is: " + self.std_log)
                continue

            # backslash handling
            if directory.endswith('/'):
                file_path = directory + file
            else:
                file_path = directory + '/' + file

            if os.path.isfile(file_path):
                if self.validate_file(file_path):
                    valid_dir_files.append(file_path)

            elif self.recursive:
                # total = total -1
                # extend files by searching through this directory
                valid_dir_files.extend(
                    self.validate_dir(file_path, progress_details))
            else:
                logging.debug(
                    f"Found subfolder: "
                    f"{file_path}"
                    f", it will be ignored")

        return valid_dir_files

    def htcompact_validation(self, file_list):
        """
        Function designed especially for this script.

        Filters given files for valid HTCondor log files,
        the process will be visual presented by rich.progress

        :param file_list: list of HTCondor logs, that need to be validated
        :return: list with valid HTCondor log files
        """
        valid_files = list()
        total = len(file_list)

        logging.info('Validate given log files')
        with Progress(transient=True) as progress:

            task = progress.add_task("Validating...", total=total, start=False)
            for arg in file_list:

                path = os.getcwd()  # mainly search in cwd
                logs_path = path + "/" + arg  # absolute path

                working_dir_path = ""
                working_file_path = ""

                if os.path.isdir(arg):
                    working_dir_path = arg
                elif os.path.isdir(logs_path):
                    working_dir_path = logs_path

                elif os.path.isfile(arg):
                    working_file_path = arg
                elif os.path.isfile(logs_path):
                    working_file_path = logs_path
                # check if only the id was given
                # and resolve it with the std_log specification
                elif os.path.isfile(arg + self.std_log):
                    working_file_path = arg + self.std_log
                elif os.path.isfile(logs_path + self.std_log):
                    working_file_path = logs_path + self.std_log

                # if path is a directory
                if working_dir_path.__ne__(""):

                    progress_details = progress, task, total, 1
                    valid_dir_files = self.validate_dir(working_dir_path,
                                                        progress_details)
                    valid_files.extend(valid_dir_files)

                # else if path "might" be a valid HTCondor file
                elif working_file_path.__ne__(""):
                    progress.update(task, advance=1)

                    if self.validate_file(working_file_path):
                        valid_files.append(working_file_path)
                    else:
                        progress.console.print(
                            f"[yellow]The given file {working_file_path} "
                            f"is not a valid HTCondor log file[/yellow]")

                else:
                    logging.error(f"The given file: {arg} does not exist")
                    rprint(f"[red]The given file: {arg} does not exist[/red]")

        return valid_files
