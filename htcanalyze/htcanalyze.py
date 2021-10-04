"""module to summarize and analyze HTCondor log files."""

import logging
import os

from typing import List
from rich import print as rprint
from rich.progress import Progress, track


# import own module
from .log_analyzer import CondorLog, get_condor_log


class HTCAnalyze:
    """
    This class is able to analyze HTCondor Joblogs.

    The modes:
        analyze,
        summarize,
        analyzed-summary

    """

    def __init__(
            self,
            show_list=None,
            rdns_lookup=None,
            tolerated_usage=None,
            bad_usage=None,
            show_legend=True
    ):

        self.show_list = [] if show_list is None else show_list

        self.rdns_cache = {}
        self.rdns_lookup = False if rdns_lookup is None else rdns_lookup

        self.tolerated_usage = 0.1 if \
            tolerated_usage is None else tolerated_usage
        self.bad_usage = 0.25 if bad_usage is None else bad_usage

        self.show_legend = show_legend  # relevant for histogram

    @staticmethod
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

    def analyze_logs(self, log_files: List[str]) -> List[CondorLog]:
        """
        Analyze the given log files one by one.

        :param log_files: list of valid HTCondor log files
        :return: list with information of each log file
        """
        logging.info('Starting the analyze mode')

        if not log_files:
            raise_value_error("No files to analyze")

        result_list = []

        # create progressbar, do not redirect output
        with Progress(
                transient=True,
                redirect_stdout=False,
                redirect_stderr=False
        ) as progress:

            task = progress.add_task("Analysing...", total=len(log_files))

            for file in log_files:
                progress.update(task, advance=1)

                condor_log = get_condor_log(file)
                result_list.append(condor_log)

        return result_list

    # def summarize(self, log_files: List[str]) -> List[dict]:
    #     """
    #     Summarize log files and analyze the results.
    #
    #     This is meant to give the ultimate output
    #     about every single job state in average etc.
    #
    #     Creates information based on the job state.
    #     The common states are:
    #     - Normal termination
    #     - Abnormal termination
    #     - Waiting for execution
    #     - Currently executing
    #     - Aborted
    #     - Aborted before submission
    #     - Aborted before execution
    #     - error while reading
    #
    #     :return: list of log information based on the job state
    #     """
    #     logging.info('Starting the analyzed summary mode')
    #
    #     # no given files
    #     if not log_files:
    #         raise_value_error("No files for the analyzed-summary")
    #
    #     # fill this dict with information by the execution type of the jobs
    #     all_files = {}
    #     occurrence_dict = {}
    #
    #     for file in track(
    #             log_files, transient=True, description="Summarizing..."
    #     ):
    #
    #         condor_event_handler = CondorEventHandler()
    #         condor_log = condor_event_handler.get_condor_log(file)
    #
    #         if occurred_errors:
    #             n_event_err = len(occurred_errors["Event Number"])
    #             occurred_errors['File'] = [file] * n_event_err
    #
    #         to_host = job_details.executing_on
    #
    #         cur_state = job_details.state
    #
    #         tt_time = time_manager.total_runtime
    #
    #         # new entry
    #         if cur_state not in all_files:
    #             # if host exists
    #             host_nodes = HostNodes(self.rdns_lookup)
    #             if job_details.executing_on:
    #                 host_nodes.add_node(SingleNode(to_host, tt_time))
    #             # else if aborted
    #             elif cur_state == 'aborted':
    #                 # aborted before submission
    #                 if not job_details.submitted_by:
    #                     host_nodes.add_node(
    #                         SingleNode('Aborted before submission', tt_time)
    #                     )
    #                 # aborted before executing
    #                 else:
    #                     host_nodes.add_node(
    #                         SingleNode('Aborted before execution', tt_time)
    #                     )
    #             # else waiting or executing
    #             elif cur_state in ['waiting', 'executing']:
    #                 host_nodes.add_node(
    #                     SingleNode('Waiting for execution', tt_time)
    #                 )
    #             else:
    #                 rprint("[red]Situation not handled yet[/red]")
    #
    #             all_files[cur_state] = {"occurrence": 1,
    #                                     "time_managers": [time_manager],
    #                                     "job_resources": [job_resources],
    #                                     "host_nodes": host_nodes,
    #                                     "errors": occurred_errors}
    #         else:
    #             # logging.debug(all_files[termination_type])
    #             all_files[cur_state]["occurrence"] += 1  # count number
    #             all_files[cur_state]["time_managers"].append(time_manager)
    #
    #             # add errors
    #             if occurred_errors:
    #                 for key, val in occurred_errors.items():
    #                     # extend if already existent
    #                     if key in all_files[cur_state]["errors"].keys():
    #                         all_files[cur_state]["errors"][key].extend(val)
    #                     else:
    #                         all_files[cur_state]["errors"] = occurred_errors
    #
    #             # resources not empty
    #             if all_files[cur_state]["job_resources"] and job_resources:
    #                 all_files[cur_state]["job_resources"].append(job_resources)
    #
    #             cur_host_nodes = all_files[cur_state]["host_nodes"]
    #             # add cpu if not None
    #             if to_host is not None:
    #                 cur_host_nodes.add_node(
    #                     SingleNode(to_host, tt_time)
    #                 )
    #             # is state aborted
    #             elif cur_state == 'aborted':
    #                 # aborted before submission
    #                 if not job_details.submitted_by:
    #                     cur_host_nodes.add_node(
    #                         SingleNode('Aborted before submission', tt_time)
    #                     )
    #                 # aborted before executing
    #                 else:
    #                     cur_host_nodes.add_node(
    #                         SingleNode('Aborted before execution', tt_time)
    #                     )
    #             # else waiting or executing
    #             elif cur_state in ['waiting', 'executing']:
    #                 cur_host_nodes.add_node(
    #                     SingleNode('Waiting for execution', tt_time)
    #                 )
    #             else:
    #                 rprint("[red]Situation not handled yet[/red]")
    #
    #     # Now put everything together
    #     result_list = []
    #     for cur_state, val in all_files.items():
    #         state_info = val
    #         result_dict = {}
    #         f_state = format_job_state(cur_state)
    #
    #         # differentiate between terminated and running processes
    #         if "error_while_reading" in cur_state:
    #             result_dict["description"] = "" \
    #                  "##################################################\n" \
    #                  "## All files, that caused an [red]" \
    #                  "error while reading[/red]\n" \
    #                  "##################################################"
    #         elif cur_state in ["waiting", "executing"]:
    #             result_dict["description"] = f"" \
    #                 f"###########################################\n" \
    #                 f"## All files, that are currently " \
    #                 f"{f_state}\n" \
    #                 f"###########################################"
    #         else:
    #             result_dict["description"] = f"" \
    #                 f"##################################################\n" \
    #                 f"## All files with the termination state: " \
    #                 f"{f_state}\n"\
    #                 f"##################################################"
    #
    #         n_jobs_with_state = int(state_info["occurrence"])
    #         occurrence_dict[f_state] = str(n_jobs_with_state)
    #
    #         result_dict["times"] = calc_avg_on_times(
    #             state_info["time_managers"])
    #
    #         if state_info["job_resources"]:
    #             avg_resources = create_avg_on_resources(
    #                 state_info["job_resources"])
    #             result_dict["all-resources"] = avg_resources
    #
    #         host_nodes_dict = state_info["host_nodes"].nodes_to_avg_dict()
    #
    #         result_dict["host-nodes"] = \
    #             sort_dict_by_col(host_nodes_dict, "Executed Jobs")
    #
    #         if state_info["errors"]:
    #             temp_err = state_info["errors"]
    #             del temp_err["Reason"]  # remove reason
    #             result_dict["errors"] = temp_err
    #
    #         result_list.append(result_dict)
    #
    #     new_occ = {
    #         "Termination type": list(occurrence_dict.keys()),
    #         "Appearance": list(occurrence_dict.values())
    #     }
    #     sorted_occ = sort_dict_by_col(new_occ, "Appearance")
    #
    #     result_list.insert(0, {"execution-details": sorted_occ})
    #
    #     return result_list
    #

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
