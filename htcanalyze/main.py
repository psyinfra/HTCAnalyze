"""

Handle config setup and commandline arguments.

Exit Codes:
    Normal Termination: 0
    No given files: 1
    Wrong Options or Arguments: 2
    TypeError: 3
    Keyboard interruption: 4

"""

import datetime
import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from typing import List

import configargparse

from htcanalyze.htcanalyze import HTCAnalyze, raise_value_error
from htcanalyze.logvalidator import LogValidator
from rich import print as rprint, box
from rich.progress import Table

# typing identities
log_inf_list = List[dict]
list_of_logs = List[str]
date_time = datetime.datetime
timedelta = datetime.timedelta

# global variables
ALLOWED_MODES = {"a": "analyze",
                 "s": "summarize",
                 "as": "analyzed-summary",
                 "d": "default"}

ALLOWED_SHOW_VALUES = ["std-err", "std-out"]
ALLOWED_IGNORE_VALUES = ["execution-details", "times", "host-nodes",
                         "used-resources", "requested-resources",
                         "allocated-resources", "all-resources",
                         "errors"]


# class to store and change global variables
class GlobalPlayer(object):
    """handle global variables."""

    def __init__(self):
        """initialize."""
        self.redirecting_stdout = None
        self.reading_stdin = None
        self.stdin_input = None

    def reset(self):
        """reset variables."""
        self.redirecting_stdout = None
        self.reading_stdin = None
        self.stdin_input = None

    def check_for_redirection(self):
        """
        Check if reading from stdin or redirecting stdout.

        It changes the global variables of GlobalServant,
        if stdin or stdout is set

        :return:
        """
        self.redirecting_stdout = not sys.stdout.isatty()
        self.reading_stdin = not sys.stdin.isatty()

        if self.reading_stdin:
            self.stdin_input = sys.stdin.readlines()


###############################
GlobalServant = GlobalPlayer()
###############################


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
        else:
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
                       default_config_files=default_config_files)

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
                             "if no file is specified, default: htcanalyze.log")

    all_vals = []
    for item in ALLOWED_MODES.items():
        all_vals.extend(list(item))

    parser.add_argument("-m", "--mode",
                        help="Specifiy an interpretation mode",
                        choices=all_vals)

    parser.add_argument("-s", dest="summarize_mode",
                        help="Short for --mode summarize,"
                             " combine with -a for analyzed-summary mode",
                        action="store_true")

    parser.add_argument("-a", dest="analyze_mode",
                        help="Short for --mode analyze,"
                             " combine with -s for analyzed-summary mode",
                        action="store_true")

    parser.add_argument("--ext-log",
                        help="Specify the log file suffix",
                        type=str)
    parser.add_argument("--ext-out",
                        help="Specify the output file suffix",
                        type=str)
    parser.add_argument("--ext-err",
                        help="Specify the error file suffix",
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
    parser.add_argument("--extend",
                        action="store_true",
                        dest="filter_extended",
                        default=None,
                        help="extend the filter keyword list "
                             "by specific error keywords")

    parser.add_argument("--reverse-dns-lookup",
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
    parser.add_argument("--save-config",
                        is_write_out_config_file_arg=True,
                        help="Stores the current configuration"
                             " into a config file")

    return parser


def manage_params(args: list) -> dict:
    """
    manage params.

    returns a dict looking like (default):

     {'verbose': False,
      'generate_log_file': None,
      'mode': None,
      'ext_log': '',
      'ext_out': '.out',
      'ext_err': '.err',
      'ignore_list': [],
      'show_list': [],
      'no_config': False,
      'filter_keywords': [],
      'extend': False,
      'reverse_dns_lookup': False
      'files': []
      ....
      }

    :param args: list of args
    :return: dict with params
    """
    # listen to stdin and add these files
    if GlobalServant.reading_stdin:
        logging.debug("Listening to arguments from stdin")
        for line in GlobalServant.stdin_input:
            args.extend(line.rstrip('\n').split(" "))

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
            print("htcanalyze: error: conflict between"
                  " --no-config and --config")
            sys.exit(2)
        # else add config again
        args.extend(["--config", prio_parsed.config[0]])

    # parse config file if not --no-config is set, might change nothing
    if not prio_parsed.no_config:
        config_paths = ['/etc/htcanalyze.conf',
                        '~/.config/htcanalyze/htcanalyze.conf',
                        sys.prefix + '/config/htcanalyze.conf']
        cmd_parser = setup_commandline_parser(config_paths)
        commands_parsed = cmd_parser.parse_args(args)
        cmd_dict = vars(commands_parsed).copy()

        # extend files list by given paths
        for log_paths in commands_parsed.path:
            files_list.extend(log_paths)
        # add files, if none are given by terminal
        if len(files_list) == 0:
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

    # parse the mode correctly
    if commands_parsed.analyze_mode and commands_parsed.summarize_mode:
        mode = "analyzed-summary"
    elif commands_parsed.analyze_mode:
        mode = "analyze"
    elif commands_parsed.summarize_mode:
        mode = "summarize"
    elif commands_parsed.mode is not None:
        if commands_parsed.mode in ALLOWED_MODES.keys():
            mode = ALLOWED_MODES[commands_parsed.mode]
        else:
            mode = commands_parsed.mode
    else:
        mode = None  # will result in default mode

    cmd_dict["mode"] = mode
    # error handling
    try:
        if cmd_dict["filter_extended"] and\
                len(cmd_dict["filter_keywords"]) == 0:
            raise_value_error("--extend not allowed without --filter")
        if len(cmd_dict["show_list"]) > 0:
            if mode == "analyzed-summary" or mode == "summarize":
                raise_value_error("--show only allowed"
                                  " with default and analyze mode")
    except ValueError as err:
        print("htcanalyze: error: " + str(err))
        sys.exit(2)

    # delete unnecessary information
    del cmd_dict["summarize_mode"]
    del cmd_dict["analyze_mode"]
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
    if len(table_dict) == 0:
        return

    table = Table(title=title,
                  show_header=True,
                  header_style="bold magenta",
                  box=box.ASCII)
    headers = list(table_dict.keys())
    n_vals = 0
    for val in headers:
        table.add_column(val)
        if n_vals == 0:
            n_vals = len(table_dict[val])
        # Todo: could be reduce to one call
    for i in range(n_vals):
        new_list = list()
        # get the values from each column, convert to str
        for val in table_dict:
            new_list.append(str(table_dict[val][i]))
        table.add_row(*new_list)

    # rprint(table)
    return table


def print_results(htcanalyze: HTCAnalyze,
                  log_files: list_of_logs,
                  mode: str,
                  ignore_list=list,
                  filter_keywords=list,
                  filter_extended=False,
                  **kwargs) -> str:
    """
    Create the ouput specified by the mode.

    :param log_files:
    :param mode:
    :param ignore_list:
    :param filter_keywords:
    :param filter_extended:
    :param kwargs:
    :return:
    """
    if len(filter_keywords) > 0:
        results = htcanalyze.\
            filter_for(log_files,
                       keywords=filter_keywords,
                       extend=filter_extended,
                       mode=mode)
    elif mode.__eq__("default"):
        results = htcanalyze.default(log_files)  # force default with -d
    elif mode.__eq__("analyzed-summary"):
        results = htcanalyze.analyzed_summary(log_files)  # analyzed summary ?
    elif mode.__eq__("summarize"):
        results = htcanalyze.summarize(log_files)  # summarize information
    elif mode.__eq__("analyze"):
        show_legend = not GlobalServant.redirecting_stdout  # redirected ?
        results = htcanalyze.analyze(log_files, show_legend)  # analyze
    else:
        results = htcanalyze.default(log_files)
        # anyways try to print default output

    # This can happen, when for example the filter mode is not forwarded
    if results is None:
        sys.exit(0)

    work_with = results
    # convert result to list, if given as dict
    if isinstance(results, dict):
        work_with = [results]

    # check for ignore values
    for mystery in work_with:

        for i in mystery:
            if mystery[i] is None:
                logging.debug("This musst be fixed,"
                              " mystery['" + i + "'] is None.")
                rprint("[red]NoneType object found,"
                       " this should not happen[/red]")

        if "description" in mystery:
            rprint(mystery["description"])

        if "execution-details" in mystery:
            if "execution-details" in ignore_list:
                del mystery["execution-details"]
            else:
                table = wrap_dict_to_table(mystery["execution-details"])
                rprint(table)

        if "times" in mystery:
            if "times" in ignore_list:
                del mystery["times"]
            else:
                table = wrap_dict_to_table(mystery["times"])
                rprint(table)

        if "all-resources" in mystery:
            if "all-resources" in ignore_list:
                del mystery["all-resources"]
            else:
                if "used-resources" in ignore_list:
                    del mystery["all-resources"]["Usage"]
                if "requested-resources" in ignore_list:
                    del mystery["all-resources"]["Requested"]
                if "allocated-resources" in ignore_list:
                    del mystery["all-resources"]["Allocated"]

                table = wrap_dict_to_table(mystery["all-resources"])
                rprint(table)

        if "ram-history" in mystery:
            if "ram-history" in ignore_list:
                del mystery["ram-history"]
            elif mystery["ram-history"] is not None:
                print(mystery["ram-history"])

        if "errors" in mystery:
            if "errors" in ignore_list:
                del mystery["errors"]
            elif mystery["errors"] is not None:
                table = wrap_dict_to_table(mystery["errors"],
                                           "Occurred HTCondor errors")
                rprint(table)

        if "host-nodes" in mystery:
            if "host-nodes" in ignore_list:
                del mystery["host-nodes"]
            elif mystery["host-nodes"] is not None:
                table = wrap_dict_to_table(mystery["host-nodes"])
                rprint(table)

        # Show more section
        if "stdout" in mystery and mystery["stdout"] != "":
            rprint("\n[bold cyan]Standard output (std-out):[/bold cyan]")
            rprint(mystery["stdout"])

        if "stderr" in mystery and mystery["stderr"] != "":
            rprint("\n[bold cyan]Standard errors (std-err):[/bold cyan]")
            rprint(mystery["stderr"])

        print()


def run(commandline_args):
    """
    Run this script.

    :param commandline_args: list of args
    :return:
    """
    # before running make sure Global Parameters are set to default
    GlobalServant.reset()

    if not isinstance(commandline_args, list):
        commandline_args = commandline_args.split()

    try:
        start = date_time.now()  # start date for runtime

        GlobalServant.check_for_redirection()
        # if exit parameters are given that will interrupt this script,
        # catch them here so the config won't be unnecessary loaded
        param_dict = manage_params(commandline_args)

        setup_logging_tool(param_dict["generate_log_file"],
                           param_dict["verbose"])

        logging.debug("-------Start of htcanalyze script-------")

        htcanalyze = \
            HTCAnalyze(ext_log=param_dict["ext_log"],
                        ext_out=param_dict["ext_out"],
                        ext_err=param_dict["ext_err"],
                        show_list=param_dict["show_list"],
                        reverse_dns_lookup=param_dict["reverse_dns_lookup"],
                        tolerated_usage=param_dict["tolerated_usage"],
                        bad_usage=param_dict["bad_usage"])

        if param_dict["verbose"]:
            logging.info('Verbose mode turned on')

        if GlobalServant.reading_stdin:
            logging.debug("Reading from stdin")
        if GlobalServant.redirecting_stdout:
            logging.debug("Output is getting redirected")

        validator = LogValidator(ext_log=param_dict["ext_log"],
                                 ext_out=param_dict["ext_out"],
                                 ext_err=param_dict["ext_err"],
                                 recursive=param_dict["recursive"])

        valid_files = validator.common_validation(param_dict["files"])

        rprint(f"[green]{len(valid_files)}"
               f" valid log file(s)[/green]\n")

        if len(valid_files) == 0:
            rprint("[red]No valid HTCondor log files found[/red]")
            sys.exit(1)

        print_results(htcanalyze, log_files=valid_files, **param_dict)

        end = date_time.now()  # end date for runtime

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
