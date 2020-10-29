"""
Handle config setup and commandline arguments.

Create visible output by using htcanalyze.

Exit Codes:
    Normal Termination: 0
    No given files: 1
    Wrong Options or Arguments: 2
    TypeError: 3
    Keyboard interruption: 4
"""

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime as date_time

import configargparse
from typing import List
from rich import print as rprint, box
from rich.progress import Table

# own classes
from htcanalyze.htcanalyze import HTCAnalyze, raise_value_error
from htcanalyze.resource import resources_to_dict
from htcanalyze.logvalidator import LogValidator

ALLOWED_SHOW_VALUES = ["htc-err", "htc-out"]
ALLOWED_IGNORE_VALUES = ["execution-details", "times", "host-nodes",
                         "used-resources", "requested-resources",
                         "allocated-resources", "all-resources",
                         "errors", "ram-history"]


def setup_logging_tool(log_file=None, verbose_mode=False):
    """
        Set up the logging device.

        to generate a log file, with --generate-log-file
        or to print more descriptive output with the verbose mode to stdout

        both modes are compatible together
    :return:
    """
    # disable the loggeing tool by default
    logging.getLogger().disabled = True

    # I don't know why a root handler is already set,
    # but we have to remove him in order
    # to get just the output of our own handler
    if len(logging.root.handlers) == 1:
        default_handler = logging.root.handlers[0]
        logging.root.removeHandler(default_handler)

    # if logging tool is set to use
    if log_file is not None:
        # activate logger if not already activated
        logging.getLogger().disabled = False

        # more specific view into the script itself
        logging_file_format = '%(asctime)s - [%(funcName)s:%(lineno)d]' \
                              ' %(levelname)s : %(message)s'
        file_formatter = logging.Formatter(logging_file_format)

        handler = RotatingFileHandler(log_file, maxBytes=1000000,
                                      backupCount=1)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(file_formatter)

        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log.addHandler(handler)

    if verbose_mode:
        # activate logger if not already activated
        logging.getLogger().disabled = False

        logging_stdout_format = '%(asctime)s - %(levelname)s: %(message)s'
        stdout_formatter = logging.Formatter(logging_stdout_format)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(stdout_formatter)
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log.addHandler(stdout_handler)


class CustomFormatter(argparse.HelpFormatter):
    """

    Custom formatter for setting argparse formatter_class.

    Identical to the default formatter,
     except that very long option strings are split into two
    lines.

    Solution discussed on: https://bit.ly/32CkCWK
    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts = []
        # if the Optional doesn't take a value, format is:
        #    -s, --long
        if action.nargs == 0:
            parts.extend(action.option_strings)
        # if the Optional takes a value, format is:
        #    -s ARGS, --long ARGS
        else:
            default = action.dest.upper()
            args_string = self._format_args(action, default)
            for option_string in action.option_strings:
                parts.append('%s %s' % (option_string, args_string))
        if sum(len(s) for s in parts) < self._width - (len(parts) - 1) * 2:
            return ', '.join(parts)
        else:
            return ',\n  '.join(parts)


def setup_prioritized_parser():
    """
    Prioritized options.

    :return: parser
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-config",
                        action="store_true")
    parser.add_argument("-c", "--config", nargs=1)
    parser.add_argument("--version",
                        help="Print out extended execution details",
                        action="store_true")

    parser.add_argument("-f", "--files",
                        nargs=1,
                        action="append",
                        dest="more_files",
                        default=[],
                        help="ONE path to log file")
    return parser


def setup_commandline_parser(default_config_files=[])\
        -> configargparse.ArgumentParser:
    """
    Define parser with all arguments listed below.

    :param default_config_files: list with config file hierarchy to look for
    :return: parser
    """
    parser = configargparse.\
        ArgumentParser(formatter_class=CustomFormatter,
                       default_config_files=default_config_files,
                       description="Analyze or summarize HTCondor-Joblogs")

    parser.add_argument("path",
                        nargs="*",
                        action="append",
                        default=[],
                        help="ANY number of paths to log file(s)")
    # also to add files with different destination,
    # to be used for config file / escaping flags with action=append
    parser.add_argument("-f", "--files",
                        nargs=1,
                        action="append",
                        dest="more_files",
                        default=[],
                        help="ONE path to log file")
    parser.add_argument("-r", "--recursive",
                        action="store_true",
                        default=None,
                        help="Recursive search through directory hierarchy")

    parser.add_argument("--version",
                        help="Print out extended execution details",
                        action="store_true")

    parser.add_argument("-v", "--verbose",
                        help="Print out extended execution details",
                        action="store_true",
                        default=None)
    parser.add_argument("--generate-log-file",
                        nargs="?",
                        const="htcanalyze.log",
                        default=None,
                        help="generates output about the process,"
                             " which is mostly useful for developers, "
                             "if no file is specified,"
                             " default: htcanalyze.log")

    parser.add_argument("--one-by-one",
                        action="store_true",
                        default=None,
                        help="Analyze given files one by one")

    parser.add_argument("--ext-log",
                        help="Suffix of HTCondor job logs (default: none)",
                        type=str)
    parser.add_argument("--ext-out",
                        help="Suffix of job out logs (default: .out)",
                        type=str)
    parser.add_argument("--ext-err",
                        help="Suffix of job error logs (default: .err)",
                        type=str)

    ignore_metavar = "{" + ALLOWED_IGNORE_VALUES[0] + " ... " \
                     + ALLOWED_IGNORE_VALUES[-1] + "}"
    allowed_ign_vals = ALLOWED_IGNORE_VALUES[:]  # copying
    allowed_ign_vals.append('')  # needed so empty list are valid in config
    parser.add_argument("--ignore",
                        nargs="+",
                        action="append",
                        choices=allowed_ign_vals,
                        metavar=ignore_metavar,
                        dest="ignore_list",
                        default=[],
                        help="Ignore a section to not be printed")
    allowed_show_vals = ALLOWED_SHOW_VALUES[:]  # copying
    allowed_show_vals.append('')  # needed so empty list are valid in config
    parser.add_argument("--show",
                        nargs="+",
                        action="append",
                        dest="show_list",
                        choices=allowed_show_vals,
                        default=[],
                        help="Show more details")

    parser.add_argument("--filter",
                        nargs="+",
                        metavar="keywords",
                        help="Filter for the given keywords",
                        default=[],
                        dest="filter_keywords",
                        action="append",
                        type=str)

    parser.add_argument("--rdns-lookup",
                        action="store_true",
                        default=None,
                        help="Resolve the ip-address of an execution nodes"
                             " to their dns entry")

    parser.add_argument("--tolerated-usage",
                        type=float,
                        help="Threshold to warn the user, "
                             "when a given percentage is exceeded "
                             "between used and requested resources")

    parser.add_argument("--bad-usage",
                        type=float,
                        help="Threshold to signal overuse/waste of resources, "
                             "when a given percentage is exceeded "
                             "between used and requested resources")
    parser.add_argument("-c", "--config",
                        is_config_file=True,
                        help="ONE path to config file")
    parser.add_argument("--no-config",
                        action="store_true",
                        help="Do not search for config")

    return parser


def manage_params(args: list) -> dict:
    """
    manage params.

    returns a dict looking like (default):

     {'verbose': False,
      'generate_log_file': None,
      'ext_log': '',
      'ext_out': '.out',
      'ext_err': '.err',
      'ignore_list': [],
      'show_list': [],
      'no_config': False,
      'filter_keywords': []
      'rdns_lookup': False
      'files': []
      ....
      }

    :param args: list of args
    :return: dict with params
    """
    prio_parsed, args = setup_prioritized_parser().parse_known_args(args)
    # first of all check for prioritised/exit params
    if prio_parsed.version:
        print("Version: v1.3.0")
        sys.exit(0)

    # get files from prio_parsed
    files_list = list()
    for log_file in prio_parsed.more_files:
        files_list.extend(log_file)

    if prio_parsed.config:
        # do not use config files if --no-config flag is set
        if prio_parsed.no_config:
            # if as well config is set, exit, because of conflict
            print("htcanalyze: error: conflict between "
                  "--no-config and --config")
            sys.exit(2)
        # else add config again
        args.extend(["--config", prio_parsed.config[0]])

    # parse config file if not --no-config is set, might change nothing
    if not prio_parsed.no_config:
        config_paths = ['/etc/htcanalyze.conf',
                        '~/.config/htcanalyze/htcanalyze.conf',
                        f'{sys.prefix}/config/htcanalyze.conf']
        cmd_parser = setup_commandline_parser(config_paths)
        commands_parsed = cmd_parser.parse_args(args)
        cmd_dict = vars(commands_parsed).copy()

        # extend files list by given paths
        for log_paths in commands_parsed.path:
            files_list.extend(log_paths)
        # add files, if none are given by terminal
        if not files_list:
            for log_paths in cmd_dict["more_files"]:
                # make sure that empty strings are not getting inserted
                if len(log_paths) == 1 and log_paths[0] != "":
                    files_list.extend(log_paths)

        # remove empty string from lists, because configargparse
        # inserts empty strings, when list is empty
        for val in cmd_dict.keys():
            if isinstance(cmd_dict[val], list):
                for li in cmd_dict[val]:
                    if len(li) == 1 and li[0] == "":
                        li.remove("")

    else:
        cmd_parser = setup_commandline_parser()
        commands_parsed = cmd_parser.parse_args(args)
        # extend files list by given paths
        for li in commands_parsed.path:
            files_list.extend(li)
        cmd_dict = vars(commands_parsed).copy()

    del cmd_dict["path"]
    del cmd_dict["more_files"]
    cmd_dict["files"] = files_list

    # concat ignore list
    new_ignore_list = list()
    for li in cmd_dict["ignore_list"]:
        new_ignore_list.extend(li)
    cmd_dict["ignore_list"] = new_ignore_list

    # concat show list
    new_show_list = list()
    for li in cmd_dict["show_list"]:
        new_show_list.extend(li)
    cmd_dict["show_list"] = new_show_list

    # concat filter list
    new_filter_list = list()
    for li in cmd_dict["filter_keywords"]:
        new_filter_list.extend(li)
    cmd_dict["filter_keywords"] = new_filter_list

    # error handling
    try:
        if cmd_dict["show_list"] and not cmd_dict["one_by_one"]:
            raise_value_error("--show only allowed with analyze mode")
    except ValueError as err:
        rprint(f"[red]htcanalyze: error: {err}[/red]")
        sys.exit(2)

    # delete unnecessary information
    del cmd_dict["version"]
    del cmd_dict["no_config"]

    if cmd_dict['ext_log'] is None:
        cmd_dict['ext_log'] = ""
    if cmd_dict['ext_err'] is None:
        cmd_dict['ext_err'] = ".err"
    if cmd_dict['ext_out'] is None:
        cmd_dict['ext_out'] = ".out"

    return cmd_dict


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
    n_vals = len(next(iter(table_dict.values())))  # get len of first value
    for val in table_dict.keys():
        table.add_column(val)
    for i in range(n_vals):
        new_list = [str(table_dict[val][i]) for val in table_dict]
        table.add_row(*new_list)

    return table


def print_results(htcanalyze: HTCAnalyze,
                  log_files: List[str],
                  one_by_one: bool,
                  ignore_list=list,
                  filter_keywords=list,
                  **kwargs) -> str:
    """
    Create the output specified by the mode.

    :param htcanalyze:
    :param log_files:
    :param one_by_one:
    :param ignore_list:
    :param filter_keywords:
    :param kwargs:
    :return:
    """
    if filter_keywords:
        log_files = htcanalyze.filter_for(log_files,
                                          keywords=filter_keywords)
    if not log_files:
        print("No files to process")
        sys.exit(0)
    if one_by_one or len(log_files) == 1:
        results = htcanalyze.analyze_one_by_one(log_files)
    else:
        results = htcanalyze.summarize(log_files)

    # Allow this to happen
    if results is None:
        sys.exit(0)

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
                for resource in resource_list:
                    resource.chg_lvl_by_threholds(0.25, 0.1)
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
                table = wrap_dict_to_table(data_dict["errors"],
                                           "Occurred HTCondor errors")
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


def check_for_redirection() -> (bool, bool, list):
    """Check if reading from stdin or redirecting stdout."""
    redirecting_stdout = not sys.stdout.isatty()
    reading_stdin = not sys.stdin.isatty()
    stdin_input = None

    if reading_stdin:
        stdin_input = sys.stdin.readlines()

    return redirecting_stdout, reading_stdin, stdin_input


def run(commandline_args):
    """
    Run this script.

    :param commandline_args: list of args
    :return:
    """
    if not isinstance(commandline_args, list):
        commandline_args = commandline_args.split()

    try:
        start = date_time.now()

        redirecting_stdout, reading_stdin, std_input = check_for_redirection()

        if reading_stdin and std_input is not None:
            for line in std_input:
                commandline_args.extend(line.rstrip('\n').split(" "))

        param_dict = manage_params(commandline_args)

        setup_logging_tool(param_dict["generate_log_file"],
                           param_dict["verbose"])

        logging.debug("-------Start of htcanalyze script-------")

        # do not show legend, if output is redirected
        show_legend = not redirecting_stdout
        htcanalyze = HTCAnalyze(
            ext_log=param_dict["ext_log"],
            ext_out=param_dict["ext_out"],
            ext_err=param_dict["ext_err"],
            show_list=param_dict["show_list"],
            rdns_lookup=param_dict["rdns_lookup"],
            tolerated_usage=param_dict["tolerated_usage"],
            bad_usage=param_dict["bad_usage"],
            show_legend=show_legend
        )

        if param_dict["verbose"]:
            logging.info('Verbose mode turned on')

        if reading_stdin:
            logging.debug("Reading from stdin")
        if redirecting_stdout:
            logging.debug("Output is getting redirected")

        validator = LogValidator(ext_log=param_dict["ext_log"],
                                 ext_out=param_dict["ext_out"],
                                 ext_err=param_dict["ext_err"],
                                 recursive=param_dict["recursive"])

        valid_files = validator.common_validation(param_dict["files"])

        rprint(f"[green]{len(valid_files)}"
               f" valid log file(s)[/green]\n")

        if not valid_files:
            rprint("[red]No valid HTCondor log files found[/red]")
            sys.exit(1)

        print_results(htcanalyze, log_files=valid_files, **param_dict)

        end = date_time.now()

        logging.debug(f"Runtime: {end - start}")  # runtime of this script

        logging.debug("-------End of htcanalyze script-------")

        sys.exit(0)

    except TypeError as err:
        logging.exception(err)
        rprint(f"[red]{err.__class__.__name__}: {err}[/red]")
        sys.exit(3)

    except KeyboardInterrupt:
        logging.info("Script was interrupted by the user")
        print("Script was interrupted")
        sys.exit(4)


def main():
    """main function (entry point)."""
    run(sys.argv[1:])


if __name__ == "main":
    """execute module."""
    main()
