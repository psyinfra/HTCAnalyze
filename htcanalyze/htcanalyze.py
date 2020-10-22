"""module to summarize and analyze HTCondor log files."""

import datetime
import logging
import os
import re
import socket
import sys

from plotille import Figure
from htcondor import JobEventLog, JobEventType as jet
import numpy as np

from rich import print as rprint
from rich.progress import Progress, track
from typing import List

# typing identities
log_inf_list = List[dict]
list_of_logs = List[str]
date_time = datetime.datetime
timedelta = datetime.timedelta


class HTCAnalyze:
    """
    This class is able to analyze HTCondor Joblogs.

    The modes:
        analyze,
        summarize,
        analyzed-summary,
        filter_for

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

    def manage_thresholds(self, resources: dict) -> dict:
        """
        Manage thresholds.

        The important part is that the keywords exist
        "Usage", "Requested"

        :param resources: a dict like:
        {
            "Resources": ["Cpu", "Disk", "Memory"]
            "Usage": [0, 13, 144]
            "Requested": [1, 1000, 6000]
            "Allocated": [1, 3000, 134900]
        }
        :return: resources with colors on usage column
        """
        # change to list, to avoid numpy type errors
        resources.update(Usage=list(resources["Usage"]))
        n_resources = len(resources['Resources'])

        for i in range(n_resources):
            # thresholds used vs. requested
            if float(resources['Requested'][i]) != 0:  # avoid division by 0

                deviation = float(resources['Usage'][i]) / float(
                    resources['Requested'][i])

                if not 1 - self.bad_usage <= deviation <= 1 + self.bad_usage:
                    level = 'error'
                elif not 1 - self.tolerated_usage <= \
                         deviation <= 1 + self.tolerated_usage:
                    level = 'warning'
                elif str(resources['Usage'][i]) == 'nan':
                    level = 'light_warning'
                else:
                    level = 'normal'

                line_color = self.get_color(level)
                resources['Usage'][i] = f"[{line_color}]" \
                    f"{resources['Usage'][i]}[/{line_color}]"

        return resources

    @classmethod
    def get_color(cls, level: str) -> str:
        colors = {'error': 'red', 'warning': 'yellow',
                  'light_warning': 'yellow2', 'normal': 'green'}
        return colors[level]

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

    def log_to_dict(self, file: str, sec: int = 0
                    ) -> (dict, dict, dict, dict, dict):
        """
        Read the log file with the htcondor module.

        Return five dicts holding information about:
        execution node, used resources, times, used ram history and errors

        :type file: str
        :param file: HTCondor log file
        :param sec: seconds to wait for new events
        :return: job_dict, res_dict, time_dict, ram_history, errors

        Consider that the return values can be None or empty dictionarys
        """
        job_events = list()
        res_dict = dict()
        time_dict = {
            "Submission date": None,
            "Execution date": None,
            "Termination date": None
        }
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
                time_dict["Submission date"] = date

                match_from_host = re.match(r"<(.+):[0-9]+\?(.*)>",
                                           event.get('SubmitHost'))
                if match_from_host:
                    submitted_host = match_from_host[1]
                    job_events.append(('Submitted from', submitted_host))
                # ERROR
                else:
                    invalid_file = True
                    reason = "Can't read user address"
                    occurred_errors.append(
                        [event_type_number, "Now", "invalid user address",
                         reason])
                    job_events.append(('Submitted from', "invalid user"))

                    try:
                        raise_value_error(f"Wrong submission host: {file}")
                    except ValueError as err:
                        logging.exception(err)
                        rprint(f"[red]{err.__class__.__name__}: {err}[/red]")

            # update execution date, execution node
            if event.type == jet.EXECUTE:
                time_dict["Execution date"] = date

                match_to_host = re.match(r"<(.+):[0-9]+\?(.*)>",
                                         event.get('ExecuteHost'))
                if match_to_host:
                    execution_host = match_to_host[1]
                    if self.rdns_lookup:  # resolve
                        execution_host = \
                            self.gethostbyaddrcached(execution_host)

                    job_events.append(('Executing on', execution_host))
                # ERROR
                else:
                    invalid_file = True
                    reason = "Can't read host address"
                    occurred_errors.append(
                        [event_type_number, "Now", "invalid host address",
                         reason])
                    job_events.append(('Executing on', "invalid host"))
                    try:
                        raise_value_error(f"Wrong execution host: {file}")
                    except ValueError as err:
                        logging.exception(err)
                        rprint(f"[red]{err.__class__.__name__}: {err}[/red]")

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
                time_dict["Termination date"] = date

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

                # put the data in the dict
                res_dict = {
                    "Resources": ["Cpu", "Disk", "Memory"],
                    "Usage": np.array(
                        [cpu_usage, disk_usage, memory_usage],
                        dtype=np.float64),
                    "Requested": np.array(
                        [cpu_requested, disk_requested, memory_requested],
                        dtype=np.float64),
                    "Allocated": np.array(
                        [cpu_allocated, disk_allocated, memory_allocated],
                        dtype=np.float64)
                }
                normal_termination = event.get('TerminatedNormally')
                # differentiate between normal and abnormal termination
                if normal_termination:
                    job_events.insert(0, ("Termination State",
                                          "[green]Normal[/green]"))
                    return_value = event.get('ReturnValue')
                    job_events.append(("Return Value", return_value))
                else:
                    job_events.insert(0, ("Termination State",
                                          "[red]Abnormal[/red]"))
                    signal = event.get('TerminatedBySignal')
                    job_events.append(("Terminated by Signal", signal))

            # update error dict and termination date
            if event.type == jet.JOB_ABORTED:
                has_terminated = True
                time_dict["Termination date"] = date

                reason = event.get('Reason')
                occurred_errors.append(
                    [event_type_number, date.strftime("%m/%d %H:%M:%S"),
                     "Aborted", reason])
                job_events.insert(0, ("Process was", "[red]Aborted[/red]"))

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

        # generate a better time dict
        better_time_dict = gen_time_dict(*time_dict.values())

        # Job still running and file valid
        if not invalid_file and not has_terminated:
            if "Total runtime" in better_time_dict["Dates and times"]:
                rprint("[red]This is not supposed to happen,"
                       " check your code[/red]")
                state = "Strange"
            elif "Execution runtime" in better_time_dict["Dates and times"]:
                state = "Executing"
            elif "Waiting time" in better_time_dict["Dates and times"]:
                state = "Waiting"
            else:
                state = "Unknown"
            job_events.insert(0, ("Process is", f"[blue]{state}[/blue]"))
        # file not fully readable
        elif invalid_file:
            better_time_dict = dict()  # times have no meaning here
            job_events.insert(0, ("Error", "[red]Error while reading[/red]"))

        job_events_dict = dict()
        error_dict = dict()
        ram_history_dict = dict()
        # convert job_events to a nice and simple dictionary
        if job_events:
            desc, val = zip(*job_events)
            job_events_dict = {
                "Execution details": list(desc),
                "Values": list(val)
            }

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

        return (job_events_dict,
                res_dict,
                better_time_dict,
                ram_history_dict,
                error_dict)

    def gethostbyaddrcached(self, ip: str):
        """
        Get the hostname by address, with an in-memory cache.

        This prevents excessive queries to DNS servers.

        :param ip: ip represented by a string
        :return: resolved domain name, else give back the IP
        """
        try:
            # try our cache first
            return self.rdns_cache[ip]
        except KeyError:
            # do the lookup
            try:
                rdns = socket.gethostbyaddr(ip)
                logging.debug(f"rDNS lookup successful: "
                              f"{ip} resolved as {rdns[0]}")
                self.rdns_cache[ip] = rdns[0]
                return rdns[0]
            except socket.error:
                logging.debug(f"Unable to perform rDNS lookup for {ip}")
                # cache negative responses too
                self.rdns_cache[ip] = ip
                return ip

    def analyze(self, log_files: list_of_logs) -> log_inf_list:
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

                job_dict, res_dict, time_dict, \
                    ram_history, occurred_errors = self.log_to_dict(file)
                if job_dict:
                    result_dict["execution-details"] = job_dict

                if time_dict:
                    result_dict["times"] = time_dict

                if res_dict:
                    result_dict["all-resources"] = \
                        self.manage_thresholds(res_dict)

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

    def summarize(self, log_files: list_of_logs) -> log_inf_list:
        """
        Summarize all given log files.

        Runs through the log files via the log_to_dict function
        Creates average runtimes and average use of resources
        for normal terminated HTCondor Jobs.
        Other types of execution will be ignored

        :return:
        """
        logging.info('Starting the summarize mode')

        # no given files
        if not log_files:
            raise_value_error("No files to summarize")

        # allocated all different datatypes, easier to handle
        result_dict = dict()

        aborted_files = 0
        still_running = 0
        error_reading_files = 0
        other_exception = 0
        normal_runtime = timedelta()
        host_nodes = dict()

        total_usages = np.array([0, 0, 0], dtype=float)
        total_requested = np.array([0, 0, 0], dtype=float)
        total_allocated = np.array([0, 0, 0], dtype=float)

        for file in track(log_files, transient=True,
                          description="Summarizing..."):
            try:
                job_dict, res_dict, time_dict, _, _ = self.log_to_dict(file)

                # continue if Process is still running
                if job_dict['Execution details'][0].__eq__("Process is"):
                    still_running += 1
                    continue
                elif job_dict['Execution details'][0].__eq__("Process was"):
                    aborted_files += 1
                    continue
                elif job_dict['Execution details'][0].__eq__("Error"):
                    error_reading_files += 1
                    continue
                elif not job_dict:
                    logging.error(
                        "if this even get's printed out, more work is needed")
                    rprint(f"[orange3]Process of {file} is strange,\n"
                           f"don't know how to handle this yet[/orange3]")
                    other_exception += 1
                    continue

                if "Total runtime" in time_dict["Dates and times"]:
                    normal_runtime += time_dict['Values'][3]
                host = job_dict['Values'][2]
                if host in host_nodes:
                    host_nodes[host][0] += 1
                    host_nodes[host][1] += time_dict['Values'][3]
                else:
                    host_nodes[host] = [1, time_dict['Values'][3]]

                total_usages += np.nan_to_num(res_dict["Usage"])
                total_requested += np.nan_to_num(res_dict["Requested"])
                total_allocated += np.nan_to_num(res_dict["Allocated"])

            # Error ocurres when Job was aborted
            except ValueError or KeyError as err:
                logging.exception(err)
                rprint(f"[red]Error with summarizing: {file}[/red]")
                continue
            except TypeError as err:
                logging.exception(err)
                rprint(f"[red]{err.__class__.__name__}: {err}[/red]")
                sys.exit(3)

        # calc number of jobs with underlying resource usage after termination
        # better said, number of jobs, which terminated normal or abnormal
        n = len(log_files) - aborted_files - still_running \
            - other_exception - error_reading_files

        average_runtime = normal_runtime / n if n != 0 else normal_runtime
        average_runtime = timedelta(days=average_runtime.days,
                                    seconds=average_runtime.seconds)

        exec_dict = {
            "Job types": ["normal executed jobs"],
            "Occurrence": [n]
        }
        if aborted_files > 0:
            exec_dict["Job types"].append("Aborted jobs")
            exec_dict["Occurrence"].append(aborted_files)
        if still_running > 0:
            exec_dict["Job types"].append("Still running jobs")
            exec_dict["Occurrence"].append(still_running)
        if error_reading_files > 0:
            exec_dict["Job types"].append("Error while reading")
            exec_dict["Occurrence"].append(error_reading_files)
        if other_exception > 0:
            exec_dict["Job types"].append("Other exceptions")
            exec_dict["Occurrence"].append(other_exception)

        result_dict["execution-details"] = \
            sort_dict_by_col(exec_dict, "Occurrence")

        result_dict["description"] = "The following data only implies " \
                                     "on sucessful executed jobs"

        # do not even try futher if the only files
        # given have been aborted, are still running etc.
        if n == 0:
            return [result_dict]

        create_desc = "The following data implies" \
                      " only on sucessful executed jobs"
        if aborted_files > 0 or still_running > 0 \
                or other_exception > 0 or error_reading_files:
            create_desc += "\n[light_grey]" \
                           "Use the analyzed-summary mode " \
                           "for more details about the other jobs" \
                           "[/light_grey]"

        result_dict["summation-description"] = create_desc

        time_desc_list = list()
        time_value_list = list()
        if normal_runtime != timedelta(0, 0, 0):
            time_desc_list.append("Total runtime")
            time_value_list.append(normal_runtime)
        if average_runtime:
            time_desc_list.append("Average runtime")
            time_value_list.append(average_runtime)

        result_dict["times"] = {
            "Times": time_desc_list,
            "Values": time_value_list
        }

        if n != 0:  # do nothing, if all valid jobs were aborted

            average_dict = {
                "Resources": ['Average Cpu', 'Average Disk (KB)',
                              'Average Memory (MB)'],
                "Usage": np.round(total_usages / n, 4),
                "Requested": np.round(total_requested / n, 2),
                "Allocated": np.round(total_allocated / n, 2)

            }

            average_dict = self.manage_thresholds(average_dict)

            result_dict["all-resources"] = average_dict

        if host_nodes:

            executed_jobs = list()
            runtime_per_node = list()
            for val in host_nodes.values():
                executed_jobs.append(val[0])
                average_job_duration = val[1] / val[0]  # timedelta object
                runtime_per_node.append(
                    timedelta(average_job_duration.days,
                              average_job_duration.seconds)
                )

            cpu_dict = {
                "Host Nodes": list(host_nodes.keys()),
                "Executed Jobs": executed_jobs,
                "Average job duration": runtime_per_node
            }

            result_dict["host-nodes"] = sort_dict_by_col(cpu_dict,
                                                         "Executed Jobs")

        return [result_dict]

    def analyzed_summary(self, log_files: list_of_logs) -> log_inf_list:
        """
        Summarize log files and analyze the results.

        This is meant to give the ultimate output
        about every single job state in average etc.

        Creates information based on the job state.
        The common states are:
        - Normal termination
        - Abnormal termination
        - Waiting for execution
        - Currently running
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
        list_of_gpu_names = list()  # list of gpus found
        occurrence_dict = dict()

        for file in track(log_files, transient=True,
                          description="Summarizing..."):

            (job_dict, res_dict, time_dict,
             ram_history, occurred_errors) = self.log_to_dict(file)

            if occurred_errors:
                n_event_err = len(occurred_errors["Event Number"])
                occurred_errors['File'] = [file] * n_event_err

            refactor_job_dict = dict(
                zip(job_dict["Execution details"], job_dict["Values"]))
            job_keys = list(refactor_job_dict.keys())
            to_host = None
            if "Executing on" in job_keys:
                to_host = refactor_job_dict["Executing on"]

            term_type = job_dict["Values"][0]

            # if time dict exists
            time_keys = list()
            waiting_time = timedelta()
            runtime = timedelta()
            total_time = timedelta()
            if time_dict:
                refactor_time_dict = dict(
                    zip(time_dict["Dates and times"], time_dict["Values"]))
                time_keys = list(refactor_time_dict.keys())
            if "Waiting time" in time_keys:
                waiting_time = refactor_time_dict["Waiting time"]
            if "Execution runtime" in time_keys:
                runtime = refactor_time_dict["Execution runtime"]
            if "Total runtime" in time_keys:
                total_time = refactor_time_dict["Total runtime"]

            try:
                if term_type in all_files:
                    # logging.debug(all_files[termination_type])
                    all_files[term_type][0] += 1  # count number
                    all_files[term_type][1] += waiting_time
                    all_files[term_type][2] += runtime
                    all_files[term_type][3] += total_time

                    # add errors
                    if occurred_errors:
                        for key in occurred_errors.keys():
                            # extend if already existent
                            if key in all_files[term_type][6].keys():
                                all_files[term_type][6][key].extend(
                                    occurred_errors[key])
                            else:
                                all_files[term_type][6] = occurred_errors

                    # resources not empty
                    if all_files[term_type][4] and res_dict:
                        all_files[term_type][4]["Usage"] += \
                            np.nan_to_num(res_dict["Usage"])
                        # add requested
                        all_files[term_type][4][
                            "Requested"] += \
                            np.nan_to_num(res_dict["Requested"])
                        # allocated
                        all_files[term_type][4]["Allocated"] += \
                            np.nan_to_num(res_dict["Allocated"])
                    elif all_files[term_type][4]:
                        rprint(f"[yellow]{term_type}: "
                               f"has no resources[/yellow]")

                    # add cpu
                    if to_host is not None:
                        # cpu known ???
                        if to_host in all_files[term_type][5].keys():
                            all_files[term_type][5][to_host][0] += 1
                            all_files[term_type][5][to_host][
                                1] += total_time
                        else:
                            all_files[term_type][5][to_host] = [1, total_time]
                    elif "Submitted from" in job_dict["Execution details"]:
                        # other waiting jobs ???
                        if 'Waiting for execution' in \
                                all_files[term_type][5].keys():
                            all_files[term_type][5][
                                'Waiting for execution'][0] += 1
                            all_files[term_type][5][
                                'Waiting for execution'][1] += total_time
                        elif "Aborted before execution" in \
                                all_files[term_type][5].keys():
                            all_files[term_type][5][
                                'Aborted before execution'][0] += 1
                            all_files[term_type][5][
                                'Aborted before execution'][1] += total_time
                        else:
                            n_host_nodes = dict()
                            if "Aborted" in term_type:
                                n_host_nodes['Aborted before'
                                             ' execution'] = [1, total_time]
                            else:
                                n_host_nodes['Waiting for'
                                             ' execution'] = [1, total_time]
                            all_files[term_type][5] = n_host_nodes
                    else:
                        # other aborted before submission jobs ???
                        if 'Aborted before submission' in \
                                all_files[term_type][5].keys():
                            all_files[term_type][5][
                                'Aborted before submission'][0] += 1
                            all_files[term_type][5][
                                'Aborted before submission'][1] += total_time
                        else:
                            n_host_nodes = dict()
                            n_host_nodes['Aborted before '
                                         'submission'] = [1, total_time]
                            all_files[term_type][5] = n_host_nodes

                # else new entry
                else:
                    # if host exists
                    if "Executing on" in job_dict["Execution details"]:
                        # to_host = job_dict["Values"][2]
                        n_host_nodes = dict()
                        n_host_nodes[to_host] = [1, total_time]
                    # else if still waiting
                    elif "Submitted from" in job_dict["Execution details"]:
                        n_host_nodes = dict()
                        if "Aborted" in term_type:
                            n_host_nodes['Aborted before'
                                         ' execution'] = [1, total_time]
                        else:
                            n_host_nodes['Waiting for'
                                         ' execution'] = [1, total_time]
                    # else aborted before submission ?
                    else:
                        n_host_nodes = dict()
                        n_host_nodes['Aborted before'
                                     ' submission'] = [1, total_time]

                    # convert nan values to 0
                    if res_dict:
                        res_dict["Usage"] = np.nan_to_num(res_dict["Usage"])
                        res_dict["Requested"] = np.nan_to_num(
                            res_dict["Requested"])
                        res_dict["Allocated"] = np.nan_to_num(
                            res_dict["Allocated"])

                    all_files[term_type] = [1,
                                            waiting_time,
                                            runtime,
                                            total_time,
                                            res_dict,
                                            n_host_nodes,
                                            occurred_errors]

            # Error ocurres when Job was aborted
            except ValueError or KeyError as err:
                logging.exception(err)
                logging.debug(f"[red]Error with summarizing: {file}[/red]")
                rprint(f"[red]Error with summarizing: {file}[/red]")
                continue
            except TypeError as err:
                logging.exception(err)
                logging.debug(f"[red]Error with summarizing: {file}[/red]")
                rprint(f"[red] {err}[/red]")
                sys.exit(3)

        # Now put everything together
        result_list = list()
        for term_state in all_files:
            term_info = all_files[term_state]
            result_dict = dict()

            # differentiate between terminated and running processes
            if "Error while reading" in term_state:
                result_dict["description"] = "" \
                     "##################################################\n" \
                     "## All files, that caused an [red]" \
                     "error while reading[/red]\n" \
                     "##################################################"
            elif term_state not in ["Waiting", "Executing"]:
                result_dict["description"] = f"" \
                    f"##################################################\n" \
                    f"## All files with the termination state: {term_state}\n"\
                    f"##################################################"
            else:
                result_dict["description"] = f"" \
                    f"###########################################\n" \
                    f"## All files, that are currently {term_state}\n" \
                    f"###########################################"

            n = int(term_info[0])
            occurrence_dict[term_state] = str(n)

            times = np.array([term_info[1], term_info[2], term_info[3]])
            av_times = times / n
            format_av_times = [
                timedelta(days=time.days, seconds=time.seconds)
                for time in av_times]

            time_dict = {
                "Times": ["Waiting time", "Runtime", "Total"],
                "Average": format_av_times,
                "Total": times
            }

            result_dict["times"] = time_dict

            if term_info[4]:
                total_resources_dict = term_info[4]
                avg_dict = {
                    'Resources': ['Average Cpu', ' Average Disk (KB)',
                                  'Average Allocated'],
                    'Usage': np.round(
                        np.array(total_resources_dict['Usage']) / term_info[0],
                        4).tolist(),
                    'Requested': np.round(
                        np.array(total_resources_dict['Requested']) /
                        term_info[0], 2).tolist(),
                    'Allocated': np.round(
                        np.array(total_resources_dict['Allocated']) /
                        term_info[0], 2).tolist()
                }
                if 'Assigned' in total_resources_dict.keys():
                    avg_dict['Resources'].append('Gpu')
                    avg_dict['Assigned'] = ['', '', '',
                                            ", ".join(list_of_gpu_names)]

                avg_dict = self.manage_thresholds(avg_dict)
                result_dict["all-resources"] = avg_dict

            executed_jobs = list()
            runtime_per_node = list()
            for val in term_info[5].values():
                executed_jobs.append(val[0])
                average_job_duration = val[1] / val[0]
                runtime_per_node.append(
                    timedelta(average_job_duration.days,
                              average_job_duration.seconds))

            host_nodes_dict = {
                "Host Nodes": list(term_info[5].keys()),
                "Executed Jobs": executed_jobs,
                "Average job duration": runtime_per_node
            }

            result_dict["host-nodes"] = \
                sort_dict_by_col(host_nodes_dict, "Executed Jobs")

            if term_info[6]:
                temp_err = term_info[6]
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

    def filter_for(self,
                   log_files: list_of_logs,
                   keywords: list,
                   extend=False,
                   mode=None
                   ) -> log_inf_list:
        """
        Filter for given keywords.

        The keywords can be extended by:
        "err", "warn", "exception", "aborted", "abortion", "abnormal", "fatal"

        The filtering is NOT case sensitive.

        The filtered files can be analyzed, summarize, etc afterwards,
        else this function will return the files

        :param log_files:
        :param keywords:
        :param extend:
        :param mode:
        :return:
            list with dicts depending on the used mode,
            list of files if mode is None
        """
        logging.info('Starting the filter mode')

        # if the keywords are given as a string, try to create a list
        if isinstance(keywords, list):
            keyword_list = keywords
        else:
            logging.debug(
                f"Filter mode only accepts a string "
                f"or list with keywords, not {keywords}")
            raise TypeError("Expecting a list or a string")

        # if extend is set, keywords like err will
        # also look for keywords like warn exception, aborted, etc.
        if extend:  # apply some rules
            # the error list
            err_list = ["err", "warn", "exception", "aborted", "abortion",
                        "abnormal", "fatal"]

            # remove keyword if already in err_list
            for keyword in keyword_list:
                if keyword.lower() in err_list:
                    keyword_list.remove(keyword)

            keyword_list.extend(err_list)  # extend search

            rprint("[green]Keyword List was extended, "
                   "now search for these keywords:[/green]",
                   keyword_list)
        else:
            rprint("[green]Search for these keywords:[/green]", keyword_list)

        if len(keyword_list) == 1 and keyword_list[0] == "":
            logging.debug("Empty filter, don't know what to do")
            return "[yellow]" \
                   "Don't know what to do with an empty filter,\n" \
                   "if you activate the filter mode in the config file, \n" \
                   "please add a [filter] section with the filter" \
                   "_keywords = your_filter[/yellow]"

        logging.debug(f"These are the keywords to look for: {keyword_list}")

        # now search
        found_at_least_one = False
        found_logs = []
        for file in track(log_files, transient=True,
                          description="Filtering..."):
            found = False
            with open(file, "r") as read_file:
                for line in read_file:
                    for keyword in keyword_list:
                        if re.search(keyword.lower(), line.lower()):
                            if not found_at_least_one:
                                print("Matches:")
                            rprint(f"[grey74]{keyword} in:\t{file}[/grey74] ")
                            found = True
                            found_at_least_one = True
                            break
                    if found:
                        found_logs.append(file)
                        break

        return_dicts = None
        if not found_at_least_one:
            rprint("[red]Unable to find these keywords:[/red]", keyword_list)
            rprint("[red]maybe try again with similar expressions[/red]")

        elif mode is not None:
            print(f"Total count: {len(found_logs)}")
            if mode.__eq__("analyzed-summary"):
                rprint("[magenta]Give an analyzed summary"
                       " for these files[/magenta]")
                return_dicts = self.analyzed_summary(found_logs)
            elif mode.__eq__("summarize"):
                rprint("[magenta]Summarize these files[/magenta]")
                return_dicts = self.summarize(found_logs)
            elif mode.__eq__("analyze"):
                rprint("[magenta]Analyze these files[/magenta]")
                return_dicts = self.analyze(found_logs)

        return return_dicts


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


def gen_time_dict(submission_date: date_time = None,
                  execution_date: date_time = None,
                  termination_date: date_time = None
                  ) -> (timedelta, timedelta, timedelta):
    """
    Generate a time dict.

    Takes in three dates, return the timedelta objects.
    Depending on the given arguments,
    this function will try to calculate
    the time differences between the events.
    If not all three values are given, it will return None

    :param submission_date: Job Sumbission date from the user
    :param execution_date: The date when the job actually started executing
    :param termination_date: The date when the job was finished
    :return: (waiting_time, runtime, total_time)

    """
    if not any(locals().values()):  # all params are None
        return None

    waiting_time = None
    runtime = None
    total_time = None
    today = date_time.now()
    today = today.replace(microsecond=0)  # remove unnecessary microseconds

    time_desc = list()
    time_vals = list()
    running_over_newyear = False

    # calculate the time difference to last year,
    # if the date is higher that today of running jobs
    # this means the execution started before newyear
    if termination_date is None:
        if submission_date and submission_date > today:
            running_over_newyear = True
            submission_date = submission_date.replace(
                year=submission_date.year - 1)
        if execution_date and execution_date > today:
            running_over_newyear = True
            execution_date = execution_date.replace(
                year=execution_date.year - 1)

    if execution_date and submission_date:
        execution_date = execution_date
        # new year ?
        if submission_date > execution_date:
            running_over_newyear = True
            submission_date = submission_date.replace(
                year=submission_date.year - 1)
        waiting_time = execution_date - submission_date

    if termination_date:
        if waiting_time:
            pass
        if execution_date:
            # new year ?
            if execution_date > termination_date:
                running_over_newyear = True
                execution_date = execution_date.replace(
                    year=execution_date.year - 1)
            runtime = termination_date - execution_date
        if submission_date:
            # new year ?
            if submission_date > termination_date:
                running_over_newyear = True
                submission_date = submission_date.replace(
                    year=submission_date.year - 1)
            total_time = termination_date - submission_date
    # Process still running
    elif waiting_time:
        runtime = today - execution_date
    # Still waiting for execution
    elif submission_date:
        waiting_time = today - submission_date

    # now after collecting all available values try to produce a dict
    # if new year was hitted by one of them, show the year as well
    if running_over_newyear:
        if submission_date:
            time_desc.append("Submission date")
            time_vals.append(submission_date)
        if execution_date:
            time_desc.append("Execution date")
            time_vals.append(execution_date)
        if termination_date:
            time_desc.append("Termination date")
            time_vals.append(termination_date)
    else:
        if submission_date:
            time_desc.append("Submission date")
            time_vals.append(submission_date.strftime("%m/%d %H:%M:%S"))
        if execution_date:
            time_desc.append("Execution date")
            time_vals.append(execution_date.strftime("%m/%d %H:%M:%S"))
        if termination_date:
            time_desc.append("Termination date")
            time_vals.append(termination_date.strftime("%m/%d %H:%M:%S"))

    if waiting_time:
        time_desc.append("Waiting time")
        time_vals.append(waiting_time)
    if runtime:
        time_desc.append("Execution runtime")
        time_vals.append(runtime)
    if total_time:
        time_desc.append("Total runtime")
        time_vals.append(total_time)

    time_dict = {
        "Dates and times": time_desc,
        "Values": time_vals
    }

    return time_dict


def sort_dict_by_col(dictionary, column, reverse=True):
    """
    Sort a dictionary by the given column.

    The dictionary must have key: list items
    where all lists have the same length

    The order is reversed
    [1,4,2,3,5] -> [5,4,3,2,1]

    :param dictionary:
    :param column:
    :param reversed:
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
