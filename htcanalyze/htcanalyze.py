"""module to summarize and analyze HTCondor log files."""

import logging
import os
import re

import numpy as np
from plotille import Figure
from datetime import datetime as date_time
from htcondor import JobEventLog, JobEventType as jet
from rich import print as rprint
from rich.progress import Progress, track
from typing import List

# import own module
from htcanalyze.resource import Resource, create_avg_on_resources
from htcanalyze.time_manager import TimeManager, calc_avg_on_times
from htcanalyze.host_nodes import SingleNode, HostNodes, node_cache
from htcanalyze.job_details import JobDetails, format_job_state


class HTCAnalyze:
    """
    This class is able to analyze HTCondor Joblogs.

    The modes:
        analyze,
        summarize,
        analyzed-summary

    """

    def __init__(self,
                 ext_log="",
                 ext_err=".err",
                 ext_out=".out",
                 show_list=None,
                 rdns_lookup=None,
                 tolerated_usage=None,
                 bad_usage=None,
                 show_legend=True):
        self.ext_log = ext_log
        self.ext_err = ext_err
        self.ext_out = ext_out

        self.show_list = [] if show_list is None else show_list

        self.rdns_cache = dict()
        self.rdns_lookup = False if rdns_lookup is None else rdns_lookup

        self.tolerated_usage = 0.1 if \
            tolerated_usage is None else tolerated_usage
        self.bad_usage = 0.25 if bad_usage is None else bad_usage

        self.show_legend = show_legend  # relevant for histogram

    def read_file(self, file: str, file_ext):
        """
        Read a file.

        :param: file
        :return: content
        """
        output_string = ""
        try:

            if os.path.getsize(file) == 0:
                return output_string

            with open(file, "r") as output_content:
                output_string = output_content.read()
        except NameError as err:
            self.handle_name_error(err, file_ext)
        except FileNotFoundError:
            self.handle_filenotfound_error(file, file_ext)
        except TypeError as err:
            logging.exception(err)
        finally:
            return output_string

    @classmethod
    def handle_name_error(cls, err, file_ext):
        """
        Handle NameError.

        :param err: An exception
        :param file_ext: file extension
        :return: None
        """
        logging.exception(err)
        rprint(f"[red]The smart_output method requires a "
               f"{file_ext} file as parameter[/red]")

    @classmethod
    def handle_filenotfound_error(cls, file, file_ext):
        """
        Handle FileNotFoundError.

        :param file: file that was not found
        :param file_ext: file extension
        :return: None
        """
        relevant = file.split(os.path.sep)[-2:]
        # match the file on ProcessID_ClusterID, if possible
        match = re.match(r".*?([0-9]{3,}_[0-9]+)" + file_ext, relevant[1])
        rprint(
            f"[yellow]There is no related {file_ext} "
            f"file: {relevant[1]} in the directory:\n"
            f"[/yellow][cyan]'{os.path.abspath(relevant[0])}'\n"
            f"with the prefix: {match[1]}[/cyan]"
        )

    def htcondor_stderr(self, file: str) -> str:
        """
        Read HTCondor stderr files.

        :param file: HTCondor stderr file
        :return: filtered content
        """
        output_string = ""

        for line in self.read_file(file, self.ext_err):
            line = line.strip("\n")
            if "err" in line.lower():
                output_string += f"[red]{line}[/red]\n"
            elif "warn" in line.lower():
                output_string += f"[yellow]{line}[/yellow]\n"

        return output_string

    def htcondor_stdout(self, file: str) -> str:
        """
        Read HTCondor stdout files.

        :param: HTCondor stdout file
        :return: content
        """
        return self.read_file(file, self.ext_out)

    def get_job_spec_id(self, file: str) -> str:
        """
        Get job specification id from a HTCondor file.

        Insert a HTCondor file cut of the suffix,
         to get just the job specification id

        Example:
        get_job_spec_id("43221_23.log", ".log") -> "43221_23"

        :param file:
        :param ext_log:
        :return: file prefix
        """
        if self.ext_log.__ne__("") \
                and file[-len(self.ext_log):].__eq__(self.ext_log):
            job_spec_id = file[:-len(self.ext_log)]
        else:
            job_spec_id = os.path.splitext(file)[0]
        return job_spec_id

    @staticmethod
    def log_to_dict(
            file: str,
            sec: int = 0
    ) -> (JobDetails,
          List[Resource],
          TimeManager,
          dict,
          dict):
        """
        Read the log file with the htcondor module.

        Return five dicts holding information about:
        execution node, used resources, times, used ram history and errors

        :type file: str
        :param file: HTCondor log file
        :param sec: seconds to wait for new events
        :return: job_details, resources, time_manager, ram_history, errors

        Consider that the return values can be None or empty dictionaries
        """
        job_details = JobDetails()
        resources = list()
        submission_date = None
        execution_date = None
        termination_date = None
        ram_history = list()
        occurred_errors = list()

        has_terminated = False
        invalid_file = False

        jel = JobEventLog(file)
        events = list()

        try:
            # Read all currently-available events
            # waiting for 'sec' seconds for the next event.
            for event in jel.events(sec):
                events.append(event)

        except OSError as err:
            logging.exception(err)
            invalid_file = True
            if err.args[0] == "ULOG_RD_ERROR":
                rprint(f"[red]{err}: {file}[/red]")
                reason = "Error while reading log file. " \
                         "File was manipulated or contains gpu usage."
                occurred_errors.append(
                    ["None", "Now", "ULOG_RD_ERROR", reason])
            else:
                rprint(f"[red]Not able to open the file: {file}[/red]")

        for event in events:
            event_type_number = event.get('EventTypeNumber')
            # convert time to datetime object
            date = date_time.strptime(event.get('EventTime'),
                                      "%Y-%m-%dT%H:%M:%S")
            # update submit date, submission host
            if event.type == jet.SUBMIT:
                submission_date = date

                match_from_host = re.match(r"<(.+):[0-9]+\?(.*)>",
                                           event.get('SubmitHost'))
                if match_from_host:
                    submitted_host = match_from_host[1]
                    job_details.submitted_by = submitted_host
                # ERROR
                else:
                    invalid_file = True
                    reason = "Can't read user address"
                    occurred_errors.append(
                        [event_type_number, "Now", "invalid user address",
                         reason])
                    job_details.submitted_by = "invalid user"

                    rprint(f"[red]Wrong submission host: {file}[/red]")

            # update execution date, execution node
            if event.type == jet.EXECUTE:
                execution_date = date

                match_to_host = re.match(r"<(.+):[0-9]+\?(.*)>",
                                         event.get('ExecuteHost'))
                if match_to_host:
                    execution_host = match_to_host[1]
                    job_details.executing_on = execution_host
                # ERROR
                else:
                    invalid_file = True
                    reason = "Can't read host address"
                    occurred_errors.append(
                        [event_type_number, "Now", "invalid host address",
                         reason])
                    job_details.executing_on = "invalid host"
                    rprint(f"[red]Wrong execution host: {file}[]/red]")

            # update ram history dict
            if event.type == jet.IMAGE_SIZE:
                size_update = event.get('Size')
                memory_usage = event.get('MemoryUsage')
                resident_set_size = event.get('ResidentSetSize')
                ram_history.append((date, size_update, memory_usage,
                                    resident_set_size))

            # update resource dict and termination date
            if event.type == jet.JOB_TERMINATED:
                has_terminated = True
                termination_date = date

                # get all resources, replace by np.nan if value is None
                cpu_usage = event.get('CpusUsage', np.nan)
                cpu_requested = event.get('RequestCpus', np.nan)
                cpu_allocated = event.get('Cpus', np.nan)
                disk_usage = event.get('DiskUsage', np.nan)
                disk_requested = event.get('RequestDisk', np.nan)
                disk_allocated = event.get("Disk", np.nan)
                memory_usage = event.get('MemoryUsage', np.nan)
                memory_requested = event.get('RequestMemory', np.nan)
                memory_allocated = event.get('Memory', np.nan)

                # create list with resources
                resources = [Resource("CPU",
                                      cpu_usage,
                                      cpu_requested,
                                      cpu_allocated),
                             Resource("Disk (KB)",
                                      disk_usage,
                                      disk_requested,
                                      disk_allocated),
                             Resource("Memory (MB)",
                                      memory_usage,
                                      memory_requested,
                                      memory_allocated)]

                normal_termination = event.get('TerminatedNormally')

                job_details.state_desc = "Termination State"
                # differentiate between normal and abnormal termination
                if normal_termination:
                    job_details.state = 'normal'
                    return_value = event.get('ReturnValue')
                    job_details.return_value = return_value
                # mostly due to signal/exit code 11
                else:
                    job_details.state = 'abnormal'
                    signal = event.get('TerminatedBySignal')
                    job_details.return_value = signal

            # update error dict and termination date
            if event.type == jet.JOB_ABORTED:
                has_terminated = True
                termination_date = date

                reason = event.get('Reason')
                occurred_errors.append(
                    [event_type_number, date.strftime("%m/%d %H:%M:%S"),
                     "Aborted", reason])
                job_details.state_desc = "Process was"
                job_details.state = 'aborted'

            # update error dict
            if event.type == jet.JOB_HELD:
                reason = event.get('HoldReason')
                occurred_errors.append(
                    [event_type_number, date.strftime("%m/%d %H:%M:%S"),
                     "JOB_HELD", reason])

            # update error dict
            if event.type == jet.SHADOW_EXCEPTION:
                reason = event.get('Message')
                occurred_errors.append((event_type_number,
                                        date.strftime("%m/%d %H:%M:%S"),
                                        "SHADOW_EXCEPTION", reason))

        # End of the file

        time_manager = TimeManager(submission_date,
                                   execution_date,
                                   termination_date)

        # Job still running and file valid
        if not invalid_file and not has_terminated:
            if time_manager.total_runtime:
                rprint("[red]This is not supposed to happen,"
                       " check your code[/red]")
                state = "strange"
            elif time_manager.execution_time:
                state = "executing"
            elif time_manager.waiting_time:
                state = "waiting"
            else:
                state = "unknown"
            job_details.state_desc = "Process is"
            job_details.state = state
        # file not fully readable
        elif invalid_file:
            time_manager = TimeManager()
            job_details.state_desc = "Error"
            job_details.state = "error_while_reading"

        error_dict = dict()
        ram_history_dict = dict()

        # convert errors into a dictionary
        if occurred_errors:
            event_numbers, time_list, errors, reasons = zip(*occurred_errors)
            error_dict = {
                "Event Number": list(event_numbers),
                "Time": list(time_list),
                "Error": list(errors),
                "Reason": list(reasons)
            }
        # convert ram_history to a dictionary
        if ram_history:
            time_list, img_size, mem_usage, res_set_size = zip(*ram_history)
            ram_history_dict = {
                "Dates": list(time_list),
                "Image size updates": list(img_size),
                "Memory usages": list(mem_usage),
                "Resident Set Sizes": list(res_set_size)
            }

        return (job_details,
                resources,
                time_manager,
                ram_history_dict,
                error_dict)

    def analyze_one_by_one(self, log_files: List[str]) -> List[dict]:
        """
        Analyze the given log files one by one.

        :param log_files: list of valid HTCondor log files
        :return: list with information of each log file
        """
        logging.info('Starting the analyze mode')

        if not log_files:
            raise_value_error("No files to analyze")

        result_list = list()

        # create progressbar, do not redirect output
        with Progress(transient=True, redirect_stdout=False,
                      redirect_stderr=False) as progress:

            task = progress.add_task("Analysing...", total=len(log_files))

            for file in log_files:
                progress.update(task, advance=1)
                result_dict = dict()

                logging.debug(f"Analysing the HTCondor log file: {file}")
                msg = f"[green]Job analysis of: {file}[/green]"
                result_dict["description"] = msg

                job_details, resources, time_manager, \
                    ram_history, occurred_errors = self.log_to_dict(file)

                if job_details.executing_on and self.rdns_lookup:
                    ip = job_details.executing_on
                    job_details.executing_on = (
                        node_cache.get_host_by_addr_cached(ip)
                    )

                result_dict["execution-details"] = job_details.to_dict()

                if time_manager:
                    result_dict["times"] = time_manager.create_time_dict()

                if resources:
                    result_dict["all-resources"] = resources

                # show HTCondor errors
                if occurred_errors:
                    result_dict["errors"] = occurred_errors

                # managing the ram history
                if ram_history:
                    ram = np.array(ram_history.get('Image size updates'))
                    dates = np.array(ram_history.get('Dates'))

                if ram_history and len(ram) > 1:
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

                    result_dict["ram-history"] = fig.show(
                        legend=self.show_legend)
                elif ram_history:
                    msg = f"Single memory update found:\n" \
                        f"Memory usage on the {dates[0]} " \
                        f"was updatet to {ram[0]} MB"
                    result_dict["ram-history"] = msg

                if self.show_list:
                    job_spec_id = self.get_job_spec_id(file)
                    if 'htc-err' in self.show_list:
                        result_dict['htc-err'] = self.htcondor_stderr(
                            job_spec_id + self.ext_err)
                    if 'htc-out' in self.show_list:
                        result_dict['htc-out'] = self.htcondor_stdout(
                            job_spec_id + self.ext_out)

                result_list.append(result_dict)

        return result_list

    def summarize(self, log_files: List[str]) -> List[dict]:
        """
        Summarize log files and analyze the results.

        This is meant to give the ultimate output
        about every single job state in average etc.

        Creates information based on the job state.
        The common states are:
        - Normal termination
        - Abnormal termination
        - Waiting for execution
        - Currently executing
        - Aborted
        - Aborted before submission
        - Aborted before execution
        - error while reading

        :return: list of log information based on the job state
        """
        logging.info('Starting the analyzed summary mode')

        # no given files
        if not log_files:
            raise_value_error("No files for the analyzed-summary")

        # fill this dict with information by the execution type of the jobs
        all_files = dict()
        occurrence_dict = dict()

        for file in track(log_files, transient=True,
                          description="Summarizing..."):

            (job_details, job_resources, time_manager,
             ram_history, occurred_errors) = self.log_to_dict(file)

            if occurred_errors:
                n_event_err = len(occurred_errors["Event Number"])
                occurred_errors['File'] = [file] * n_event_err

            to_host = job_details.executing_on

            cur_state = job_details.state

            tt_time = time_manager.total_runtime

            # new entry
            if cur_state not in all_files:
                # if host exists
                host_nodes = HostNodes(self.rdns_lookup)
                if job_details.executing_on:
                    host_nodes.add_node(SingleNode(to_host, tt_time))
                # else if aborted
                elif cur_state == 'aborted':
                    # aborted before submission
                    if not job_details.submitted_by:
                        host_nodes.add_node(
                            SingleNode('Aborted before submission', tt_time)
                        )
                    # aborted before executing
                    else:
                        host_nodes.add_node(
                            SingleNode('Aborted before execution', tt_time)
                        )
                # else waiting or executing
                elif cur_state in ['waiting', 'executing']:
                    host_nodes.add_node(
                        SingleNode('Waiting for execution', tt_time)
                    )
                else:
                    rprint("[red]Situation not handled yet[/red]")

                all_files[cur_state] = {"occurrence": 1,
                                        "time_managers": [time_manager],
                                        "job_resources": [job_resources],
                                        "host_nodes": host_nodes,
                                        "errors": occurred_errors}
            else:
                # logging.debug(all_files[termination_type])
                all_files[cur_state]["occurrence"] += 1  # count number
                all_files[cur_state]["time_managers"].append(time_manager)

                # add errors
                if occurred_errors:
                    for key in occurred_errors.keys():
                        # extend if already existent
                        if key in all_files[cur_state]["errors"].keys():
                            all_files[cur_state]["errors"][key].extend(
                                occurred_errors[key])
                        else:
                            all_files[cur_state]["errors"] = occurred_errors

                # resources not empty
                if all_files[cur_state]["job_resources"] and job_resources:
                    all_files[cur_state]["job_resources"].append(job_resources)

                cur_host_nodes = all_files[cur_state]["host_nodes"]
                # add cpu if not None
                if to_host is not None:
                    cur_host_nodes.add_node(
                        SingleNode(to_host, tt_time)
                    )
                # is state aborted
                elif cur_state == 'aborted':
                    # aborted before submission
                    if not job_details.submitted_by:
                        cur_host_nodes.add_node(
                            SingleNode('Aborted before submission', tt_time)
                        )
                    # aborted before executing
                    else:
                        cur_host_nodes.add_node(
                            SingleNode('Aborted before execution', tt_time)
                        )
                # else waiting or executing
                elif cur_state in ['waiting', 'executing']:
                    cur_host_nodes.add_node(
                        SingleNode('Waiting for execution', tt_time)
                    )
                else:
                    rprint("[red]Situation not handled yet[/red]")

        # Now put everything together
        result_list = list()
        for cur_state in all_files:
            state_info = all_files[cur_state]
            result_dict = dict()
            f_state = format_job_state(cur_state)

            # differentiate between terminated and running processes
            if "error_while_reading" in cur_state:
                result_dict["description"] = "" \
                     "##################################################\n" \
                     "## All files, that caused an [red]" \
                     "error while reading[/red]\n" \
                     "##################################################"
            elif cur_state in ["waiting", "executing"]:
                result_dict["description"] = f"" \
                    f"###########################################\n" \
                    f"## All files, that are currently " \
                    f"{f_state}\n" \
                    f"###########################################"
            else:
                result_dict["description"] = f"" \
                    f"##################################################\n" \
                    f"## All files with the termination state: " \
                    f"{f_state}\n"\
                    f"##################################################"

            n_jobs_with_state = int(state_info["occurrence"])
            occurrence_dict[f_state] = str(n_jobs_with_state)

            result_dict["times"] = calc_avg_on_times(
                state_info["time_managers"])

            if state_info["job_resources"]:
                avg_resources = create_avg_on_resources(
                    state_info["job_resources"])
                result_dict["all-resources"] = avg_resources

            host_nodes_dict = state_info["host_nodes"].nodes_to_avg_dict()

            result_dict["host-nodes"] = \
                sort_dict_by_col(host_nodes_dict, "Executed Jobs")

            if state_info["errors"]:
                temp_err = state_info["errors"]
                del temp_err["Reason"]  # remove reason
                result_dict["errors"] = temp_err

            result_list.append(result_dict)

        new_occ = {
            "Termination type": list(occurrence_dict.keys()),
            "Appearance": list(occurrence_dict.values())
        }
        sorted_occ = sort_dict_by_col(new_occ, "Appearance")

        result_list.insert(0, {"execution-details": sorted_occ})

        return result_list


def raise_value_error(message: str) -> ValueError:
    """
    Raise Value Error with message.

    :param message: str
    :return:
    """
    raise ValueError(message)


def raise_type_error(message: str) -> TypeError:
    """
    Raise Type Error with message.

    :param message:
    :return:
    """
    raise TypeError(message)


def _int_formatter(val, chars, delta, left=False):
    """
    Format float to int.

    Usage of this is shown here:
    https://github.com/tammoippen/plotille/issues/11
    """
    align = '<' if left else ''
    return '{:{}{}d}'.format(int(val), align, chars)


def sort_dict_by_col(dictionary, column, reverse=True):
    """
    Sort a dictionary by the given column.

    The dictionary must have key: list items
    where all lists have the same length

    The order is reversed
    [1,4,2,3,5] -> [5,4,3,2,1]

    :param dictionary:
    :param column:
    :param reverse:
    :return:
    """
    # sorted_dict = dict.fromkeys(dictionary.keys())
    sorted_dict = {key: [] for key in dictionary.keys()}
    sort_index = list(sorted_dict.keys()).index(column)
    zip_data = zip(*dictionary.values())
    sorted_items = sorted(zip_data, key=lambda tup: tup[sort_index])
    if reverse:
        sorted_items = reversed(sorted_items)
    for item in sorted_items:
        for i, key in enumerate(sorted_dict.keys()):
            sorted_dict[key].append(item[i])

    return sorted_dict
