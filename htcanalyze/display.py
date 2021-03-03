import logging
import sys
from typing import List

from rich import print as rprint
from rich.table import Table, box

from htcanalyze.htcanalyze import HTCAnalyze
from htcanalyze.resource import resources_to_dict

#
MAX_ERRORS = 10

# sys exit calls
NORMAL_EXECUTION = 0


def check_for_redirection() -> (bool, bool, list):
    """Check if reading from stdin or redirecting stdout."""
    redirecting_stdout = not sys.stdout.isatty()
    reading_stdin = not sys.stdin.isatty()
    stdin_input = None

    if reading_stdin:
        stdin_input = sys.stdin.readlines()

    return redirecting_stdout, reading_stdin, stdin_input


def wrap_dict_to_table(table_dict, title="") -> Table:
    """
    Wrap dict to rich table.

    Takes a dict of the format :
    {
        column1: [Header1, Header2, Header3]
        column2: [val1, val2, val3]
    }
    Why ? Because the tool tabulate took the data like this
    and this function is supposed to reduce the usage of tabulate
    without too much work
    :param table_dict:
    :param title: title of table
    :return: table
    """
    if not table_dict:
        return None

    table = Table(title=title,
                  show_header=True,
                  header_style="bold magenta",
                  box=box.ASCII)
    for val in table_dict.keys():
        table.add_column(val)

    try:
        index = 0
        while True:
            new_row = [str(table_dict[val][index]) for val in table_dict]
            table.add_row(*new_row)
            index += 1
    except IndexError:
        pass

    return table


def wrap_error_dict_to_table(
        errors, title, show_all=False, max_errors=MAX_ERRORS
):
    if not errors:
        return None
    elif show_all:
        return wrap_dict_to_table(errors, title)

    n_vals = len(next(iter(errors.values())))  # get len of first value
    if n_vals > max_errors:
        prettify_table = {}
        for event_n, time, label, file in zip(
                errors['Event Number'],
                errors['Time'],
                errors['Error'],
                errors['File'],
        ):
            if label in prettify_table.keys():
                prettify_table[label]['count'] += 1
            else:
                prettify_table[label] = {
                    'event_n': event_n,
                    'count': 1
                }

        table = Table(
            title=title,
            show_header=True,
            header_style="bold magenta",
            box=box.ASCII
        )
        table.add_column('Error')
        table.add_column('Event Number')
        table.add_column('Appearance')
        for key in prettify_table.keys():
            vals = prettify_table[key]
            row = [key, str(vals['event_n']), str(vals['count'])]
            table.add_row(*row)

    else:
        table = wrap_dict_to_table(errors, title)

    return table


def print_results(
        htcanalyze: HTCAnalyze,
        log_files: List[str],
        one_by_one: bool,
        ignore_list=list,
        **kwargs
) -> str:
    """
    Create the output specified by the mode.

    :param htcanalyze:
    :param log_files:
    :param one_by_one:
    :param ignore_list:
    :param kwargs:
    :return:
    """
    if not log_files:
        print("No files to process")
        sys.exit(NORMAL_EXECUTION)
    if one_by_one or len(log_files) == 1:
        results = htcanalyze.analyze_one_by_one(log_files)
    else:
        results = htcanalyze.summarize(log_files)

    # Allow this to happen
    if results is None:
        sys.exit(NORMAL_EXECUTION)

    # convert result to processed data list, if not a list
    proc_data_list = [results] if not isinstance(results, list) else results

    # check for ignore values
    for data_dict in proc_data_list:

        for key in data_dict:
            if data_dict[key] is None:
                logging.debug(f"This musst be fixed, "
                              f"data_dict['{key}'] is None.")
                rprint("[red]NoneType object found, "
                       "this should not happen[/red]")

        if "description" in data_dict:
            rprint(data_dict["description"])

        if "execution-details" in data_dict:
            if "execution-details" in ignore_list:
                del data_dict["execution-details"]
            elif data_dict["execution-details"]:
                table = wrap_dict_to_table(data_dict["execution-details"])
                rprint(table)

        if "times" in data_dict:
            if "times" in ignore_list:
                del data_dict["times"]
            elif data_dict["times"]:
                table = wrap_dict_to_table(data_dict["times"])
                rprint(table)

        if "all-resources" in data_dict:
            if "all-resources" in ignore_list:
                del data_dict["all-resources"]
            elif data_dict["all-resources"]:
                resource_list = data_dict["all-resources"]
                # for resource in resource_list:
                #     resource.chg_lvl_by_threholds(0.25, 0.1)
                res_dict = resources_to_dict(resource_list)
                if "used-resources" in ignore_list:
                    del res_dict["Usage"]
                if "requested-resources" in ignore_list:
                    del res_dict["Requested"]
                if "allocated-resources" in ignore_list:
                    del res_dict["Allocated"]

                table = wrap_dict_to_table(res_dict)
                rprint(table)

        if "ram-history" in data_dict:
            if "ram-history" in ignore_list:
                del data_dict["ram-history"]
            elif data_dict["ram-history"] is not None:
                print(data_dict["ram-history"])

        if "errors" in data_dict:
            if "errors" in ignore_list:
                del data_dict["errors"]
            elif data_dict["errors"] is not None:
                # table = wrap_dict_to_table(
                #     data_dict["errors"], "Occurred HTCondor errors"
                # )
                table = wrap_error_dict_to_table(
                    data_dict["errors"], "Occurred HTCondor errors"
                )
                rprint(table)

        if "host-nodes" in data_dict:
            if "host-nodes" in ignore_list:
                del data_dict["host-nodes"]
            elif data_dict["host-nodes"] is not None:
                table = wrap_dict_to_table(data_dict["host-nodes"])
                rprint(table)

        # Show more section
        if "htc-out" in data_dict and data_dict["htc-out"] != "":
            rprint("\n[bold cyan]Related HTC standard output:[/bold cyan]")
            rprint(data_dict["htc-out"])

        if "htc-err" in data_dict and data_dict["htc-err"] != "":
            rprint("\n[bold cyan]Related HTCondor standard error:[/bold cyan]")
            rprint(data_dict["htc-err"])

        print()
