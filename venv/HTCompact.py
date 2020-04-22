#! usr/bin/python
import re
import sys
import os
import getopt
import datetime
import logging

import configparser
import pandas as pd
from tabulate import tabulate

# make default changes to logging tool
logging.basicConfig(filename="stdout.log", level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s : %(message)s')

"""

Version 1.2
Maintainer: Mathis L.
Date: 02.04.2020

There are three functions, to simply read and return the content of a file,
1. read_condor_logs(file): returns two lists that are related by the same index
2. read_condor_error(file): returns a string with the content
3. read_condor_output(file): returns a string with the content

The next three functions return an output string in a "smart" way by parameters and specifications,
especially the log files will be scanned for important information,
1. smart_output_logs(file): returns important information inside a HTCondor log file
2. smart_output_error(file): returns any kind of errors
3. smart_output_output(file): returns just the output content, Todo: further specs

The next function puts all three together, also by interpreting the given parameters
smart_manage_all(cluster_process_id)


"""
# global parameters, used for dynamical output of information
files = list()
border_str = ""

# variables for given parameters
show_output = False
show_warnings = False
show_allocated_res = False
ignore_errors = False
ignore_resources = False
reverse_dns_lookup = False  # Todo: implement in function (filter_for_host)

# to store output in a csv file it's easier to save them into lists
resources_to_csv = False
job_to_csv = False
indexing = True

# escape sequences for colors
red = "\033[0;31m"
green = "\033[0;32m"
yellow = "\033[0;33m"
cyan = "\033[0;36m"
back_to_default = "\033[0;39m"

# global variables with default values for err/log/out files
std_log = ".log"
std_err = ".err"
std_out = ".out"

# global variables for tabulate
"""
Documentation: https://github.com/astanin/python-tabulate

Types:
plain, simple, github, grid, fancy_grid, pipe,
orgtbl, rst, mediawiki, html, latex, latex_raw,
latex_booktabs, tsv
default: simple)
"""
table_format = "pretty"  # ascii by deafult

# Todos:
# Todo: did a lot of test, but it needs more
# Todo: background colors etc. for terminal usage
# Todo: filter erros better, less priority
# Todo: realise the further specs on: https://jugit.fz-juelich.de/inm7/infrastructure/scripts/-/issues/1
# Todo: make global variable for err/log/out files, should be given by user if not in default form
# a redirection in the terminal via > should ignore escape sequences


# may not be needed in future but will be used for now
def ignore_spaces_in_arguments(args):
    """
        I want to make it easier for the user to insert many files at once are spaces between arguments.

        I want that this is possible: python3 HTCompact.py -f file1 file2 file3 ... -otheropts
        What sys.argv[1:] looks like : ['-f', 'file1', 'file2', 'file3', '...', '-otheropts']
        What I want to look like : ['-f', 'file1 file2 file3 ...', '-otheropts']

        !!!Exactly that is this method doing!!! (because getopt has no such function)

    :param args: is supposed to be a list, in any case it should be the sys.argv[1:] list
    :return: list, that ignores spaces in the arguments
    """
    new_list = list()
    temp_string = ""
    index = 0
    while True:
        if index < len(args):
            if args[index].startswith("-"):
                new_list.append(args[index])

            else:
                if index < len(args) - 1 and args[index + 1].startswith("-"):
                    temp_string += args[index]
                    new_list.append(temp_string)
                    temp_string = ""
                else:
                    temp_string += args[index] + " "

            index += 1
        else:
            # if the last arg is no opt, the build up string must be considered, only if not empty
            if temp_string.__ne__(""):
                new_list.append(temp_string[:-1])
            break

    return new_list


def manage_params():
    """
    Interprets the given command line arguments and changes the global variables in this scrips

    """
    global files  # list of files and directories
    global std_log, std_err, std_out  # all default values for the HTCondor files
    global show_output, show_warnings, show_allocated_res  # show more information variables
    global ignore_errors, ignore_resources  # ignore information variables
    global resources_to_csv, job_to_csv, indexing  # store the redirected output in a tabular structure
    global table_format  # table_format can be changed

    # if output gets redirected with > or | or other redirection tools, ignore escape sequences
    if not sys.stdout.isatty():
        global red, green, yellow, cyan, back_to_default
        red = ""
        green = ""
        yellow = ""
        cyan = ""
        back_to_default = ""
        logging.debug("Output is getting redirected, all escape sequences were set to \"\"")

    try:
        better_args = ignore_spaces_in_arguments(sys.argv[1:])

        # interpret the first arguments after sys.argv[0] as files/directories
        # if files are set in the config file and no files are given as argument, skip this part
        if len(better_args) > 0 and not better_args[0].startswith("-"):
            files = better_args[0].split()
            better_args = better_args[1:]  # remove them from opts

        opts, args = getopt.getopt(better_args, "h",
                                   ["help", "std-log=", "std-error=", "std-out=",
                                    "show-output", "show-warnings", "show-allocated-resources",
                                    "ignore-errors", "ignore-resources",
                                    "res-to-csv", "job-to-csv", "indexing=",
                                    "table-format="])
        # print(opts, args)
        for opt, arg in opts:
            if opt in ["-h", "--help"]:
                print(help_me())
                exit(0)

            # all HTCondor files, given by the user if they are not saved in .log/.err/.out files
            elif opt == "--std-log":
                # to forget the . should not be painful
                if arg[0] != '.':
                    arg = "."+arg
                std_log = arg
            elif opt == "--std-error":
                # to forget the . should not be painful
                if arg[0] != '.':
                    arg = "."+arg
                std_err = arg
            elif opt == "--std-out":
                # to forget the . should not be painful
                if arg[0] != '.':
                    arg = "."+arg
                std_out = arg
            # all variables, to show more specific information
            elif opt.__eq__("--show-output"):
                show_output = True
            elif opt.__eq__("--show-warnings"):
                show_warnings = True
            elif opt.__eq__("--show-allocated-resources"):
                show_allocated_res = True

            # all variables to ignore unwanted information
            elif opt.__eq__("--ignore-errors"):
                ignore_errors = True
            elif opt.__eq__("--ignore-resources"):
                ignore_resources = True

            # all tabulate variables
            elif opt.__eq__("--res-to-csv"):
                resources_to_csv = True
            elif opt.__eq__("--job-to-csv"):
                job_to_csv = True
            elif opt.__eq__("--indexing"):
                indexing = True if arg.lower() == "true" else False
            elif opt.__eq__("--table-format"):
                table_format = arg

            else:
                print(help_me())
                exit(0)

    # print error messages
    except Exception as err:
        logging.exception(err)  # write a detailed description in the stdout.log file
        print((red+"{0}: {1}"+back_to_default).format(err.__class__.__name__, err))
        print(help_me())
        exit(0)


# Todo:
def help_me():
    """
    :return:    string with instructions and specifications how to use this script
    """
    output_string = red+"Use: \"python3 " + sys.argv[0] + " -h\" for help"+back_to_default
    return output_string


# reads all information, but returns them in two lists
# Todo: read specifications from a config files,
#       cause the script is based on hardcoded interpretation for log files in
#       the form: string_clusterId_processId.log
def read_condor_logs(file):
    """

    reads a given HTCondor std_log file and separates the information in two lists,
    for further and easier access

    :param file:    a HTCondor std_log file

    :raises: :class:'FileNotFoundError': if open does not work

    :return:    (job_event, job_event_information)
                a list of job_events and a list of job_event-relevant information
                these are related by the same index like:
                job_event[1]-> relevant information: job_event_information[1]
    """

    if not file.endswith(std_log):
        raise NameError("The read_condor_logs method is only for "+std_log+" files")

    log_job_events = list()  # saves the job_events
    job_event_information = list()  # saves the information for each job event, if there are any
    temp_job_event_list = list()  # just a temporary list, gets inserted into job_event_information

    with open(file) as log_file:
        # for every line in the log_file
        for line in log_file:

            line = line.rstrip("\n")  # remove newlines
            match_log\
                = re.match(r"([0-9]{3})"  # matches event number
                           r" (\([0-9]+.[0-9]+.[0-9]{3}\))"  # matches clusterid and process id
                           r" ([0-9]{2}/[0-9]{2})"  # matches date
                           r" ([0-9]{2}:[0-9]{2}:[0-9]{2})"  # matches time
                           r"((?: \w+)*)."  # matches the job event name
                           r"(.*)", line)  # matches further information
            if match_log:
                job_event_number = match_log[1]  # job event number, can be found in job_description.txt
                clusterid_procid_inf = match_log[2]  # same numbers, that make the name of the file
                date = match_log[3]  # filter the date in the form Month/Day in numbers
                time = match_log[4]  # filter the time
                job_event_name = match_log[5]  # filter the job event name
                job_relevant_inf = match_log[6]  # filter the job relevant information

                log_job_events.append([job_event_number, clusterid_procid_inf,
                                       date, time, job_event_name, job_relevant_inf])
                # print(job_event_number, clusterid_procid_inf, date, time, job_event_name, job_relevant_inf)
            else:
                # end of job event
                if "..." in line:
                    job_event_information.append(temp_job_event_list)
                    temp_job_event_list = list()  # clear list
                    continue
                elif line.startswith("\t"):
                    temp_job_event_list.append(line)

    return log_job_events, job_event_information


# Todo: maybe less information
# just read .err files content and return it as a string
def read_condor_error(file):
    """
    Reads a HTCondor .err file and returns its content

    :param file: a HTCondor .err file

    :raises: :class:'NameError': The param file was no .err file
             :class:'FileNotFoundError': if open does not work

    :return: file content

    """
    if not file.endswith(std_err):
        raise NameError("The read_condor_error method is only for "+std_err+" files")

    err_file = open(file)
    return "".join(err_file.readlines())


# just read .out files content and return it as a string
def read_condor_output(file):
    """
        Reads a HTCondor .out file and returns its content

        :param file: a HTCondor .out file

        :raises: :class:'NameError': The param file was no .out file
                 :class:'FileNotFoundError': if open does not work

        :return: file content

        """
    if not file.endswith(std_out):
        raise NameError("The read_condor_output method is only for "+std_out+" files")

    out_file = open(file)
    return "".join(out_file.readlines())


# Todo:
def filter_for_host(ip):
    """
    this function is supposed to filter a given ip for it's representive url like jusell.inm7.de:cpu1
    :return:
    """


# Todo: gpu usage
def smart_output_logs(file):
    """
    reads a given HTCondor .log file with the read_condor_logs() function

    :param file:    a HTCondor .log file

    :return:        (output_string)
                    an output string that shows information like:
                    The job procedure of : ../logs/454_199.log
                    +-------------------+--------------------+
                    | Executing on Host |      10.0.9.1      |
                    |       Port        |        9618        |
                    |      Runtime      |      1:12:20       |
                    | Termination State | Normal termination |
                    |   Return Value    |         0          |
                    +-------------------+--------------------+
                    +--------+-------+-----------+-----------+
                    |        | Usage | Requested | Allocated |
                    +--------+-------+-----------+-----------+
                    |  Cpu   | 0.30  |     1     |     1     |
                    |  Disk  |  200  |    200    |  3770656  |
                    | Memory |   3   |     1     |    128    |
                    +--------+-------+-----------+-----------+


                    with the --csv option it looks like:

                    -------------------------------------------

                    The job procedure of : ../logs/454_199.log

                    Description,Values
                    Executing on Host,10.0.9.1
                    Port,9618
                    Runtime,1:12:20
                    Termination State,Normal termination
                    Return Value,0

                    Resources,Usage,Requested,Allocated
                    Cpu,0.30,1,1
                    Disk,200,200,3770656
                    Memory,3,1,128

                    -------------------------------------------

    """
    try:
        job_events, job_raw_information = read_condor_logs(file)
        global border_str

        output_string = ""

        if not resources_to_csv and not job_to_csv:
            output_string += green+"The job procedure of : " + file + back_to_default + "\n"
            border_str = "-" * len(output_string) + "\n"

        if job_events[-1][0].__eq__("005"):  # if the last job event is : Job terminated

            # job_executing = job_events[1][4][1:]
            host = job_events[1][5][2:10]  # Todo: what if ip address has more than 8 chars
            port = job_events[1][5][11:15]  # Todo: what if port has not 4 numbers

            # calculate the runtime for the job
            submitted_date = datetime.datetime.strptime(job_events[0][2] + " " + job_events[0][3], "%m/%d %H:%M:%S")
            terminating_date = datetime.datetime.strptime(job_events[-1][2] + " " + job_events[-1][3], "%m/%d %H:%M:%S")
            runtime = terminating_date - submitted_date  # calculation of the time runtime

            # make a fancy design for the job_information
            job_labels = ["Executing on Host", "Port", "Runtime"]  # holds the labels
            job_information = [host, port, runtime]  # holds the related job information

            # filter the termination state ...
            if True:
                # check if termination state is normal
                termination_state_inf = job_raw_information[-1][0]
                match_termination_state = re.match(r"\t\(1\) ((?:\w+ )*)", termination_state_inf)
                if match_termination_state:
                    job_labels.append("Termination State")
                    job_information.append(match_termination_state[1])

                    if "Normal termination" in match_termination_state[1]:
                        match_return_value = re.match(r"\t\(1\) (?:\w+ )*\((?:\w+ )*([0-9]+)\)", termination_state_inf)
                        return_value = match_return_value[1] if match_return_value else "None"
                        if return_value == "None":
                            print(red + "Not a valid return state in the HTCondor log file"+back_to_default)
                        else:
                            job_labels.append("Return Value")
                            job_information.append(return_value)

                else:
                    print(red + "Termination error in HTCondor log file" + back_to_default)

            # now put everything together in a pretty table
            job_df = pd.DataFrame({"Values": job_information})
            job_df = job_df.set_axis(job_labels, axis='index')

            # if job_to_csv is set
            if job_to_csv:

                # if recources_to_csv is wanted as well, keep headers
                if resources_to_csv:
                    # if indexing add column Description
                    if indexing:
                        output_string += "Description" + job_df.to_csv(index=indexing)
                    # else remove first comma
                    else:
                        output_string += job_df.to_csv(index=indexing)
                # ignore headers if no jobs get printed
                else:
                    output_string += job_df.to_csv(header=False, index=indexing)  # save as csv
            # if only recources_to_csv is set, ignore other output
            elif resources_to_csv:
                pass
            else:
                output_string += tabulate(job_df, tablefmt=table_format) + "\n"

            # ignore resources ?
            if not ignore_resources:

                relevant_str = "\n".join(job_raw_information[-1])  # job information of the last job (Job terminated)

                # next part removes not useful lines
                if True:  # just for readability
                    # remove unnecessary lines
                    lines = relevant_str.splitlines()
                    while not lines[0].startswith("\tPartitionable"):
                        lines.remove(lines[0])

                    lines.remove(lines[0])
                    partitionable_res = lines
                    # done, partitionable_resources contain now only information about used resources
                
                # match all resources
                # Todo: match even if values are missing, might get impossible if more than one value is missing
                match = re.match(r"\t *Cpus *: *([0-9]?(?:\.[0-9]{2})?) *([0-9]+) *([0-9]+)", partitionable_res[0])
                if match:
                    cpu_usage, cpu_request, cpu_allocated = match[1], match[2], match[3]
                else:
                    print(red+"Something went wrong reading the cpu information"+back_to_default)
                    return
                match = re.match(r"\t *Disk \(KB\) *: *([0-9]+) *([0-9]+) *([0-9]+)", partitionable_res[1])
                if match:
                    disk_usage, disk_request, disk_allocated = match[1], match[2], match[3]
                else:
                    print(red + "Something went wrong reading the disk information" + back_to_default)
                    return
                match = re.match(r"\t *Memory \(MB\)  *: *([0-9]+) *([0-9]+) *([0-9]+)", partitionable_res[2])
                if match:
                    memory_usage, memory_request, memory_allocated = match[1], match[2], match[3]
                else:
                    print(red + "Something went wrong reading the memory information" + back_to_default)
                    return

                # list of resources and their labels
                resource_labels = ["Cpu", "Disk", "Memory"]
                usage = [cpu_usage, disk_usage, memory_usage]
                requested = [cpu_request, disk_request, memory_request]
                allocated = [cpu_allocated, disk_allocated, memory_allocated]

                # Error handling: change empty values to NaN
                for i in range(3):
                    if usage[i] == "":
                        usage[i] = "NaN"
                    if requested[i] == "":
                        requested[i] = "NaN"
                    if allocated[i] == "":
                        allocated[i] = "NaN"

                # put the data in the DataFrame
                res_df = pd.DataFrame({
                    "Usage": usage,
                    "Requested": requested,
                    # "Allocated": allocated
                })

                # if the user wants allocated resources then add it to the DataFrame as well
                if show_allocated_res:
                    res_df.insert(2, "Allocated", allocated)

                res_df = res_df.set_axis(resource_labels, axis='index')  # make new DataFrame with resource_labels

                # if resources_to_csv is wanted
                if resources_to_csv:

                    # if job_to_csv is wanted as well, keep headers
                    if job_to_csv:
                        # if indexing add column Resources
                        if indexing:
                            output_string += "Recources"+res_df.to_csv(index=indexing)
                        # else remove first comma
                        else:
                            output_string += res_df.to_csv(index=indexing)
                    # ignore headers if no jobs get printed
                    else:
                        output_string += res_df.to_csv(header=False, index=indexing)

                # if only job_to_csv is set ignore other output
                elif job_to_csv:
                    pass  # could maybe be implemented earlier

                # normal output
                else:
                    # use tabulate to print a fancy output
                    fancy_design = tabulate(res_df, headers='keys', tablefmt=table_format)
                    output_string += fancy_design + "\n"

        # Todo: more information, maybe why ?
        elif job_events[-1][0].__eq__("009"):  # job aborted

            # job_event description, which is "Job was aborted by the user" and the user filter
            output_string += job_events[-1][4][1:] + ": " + ((job_raw_information[-1][0]).split(" ")[-1])[:-1]+"\n"

    except NameError as err:
        logging.exception(err)
        print("The smart_output_logs method requires a "+std_log+" file as parameter")
    except FileNotFoundError as err:
        logging.exception(err)
        print(red+str(err)+back_to_default)
    # finally
    else:
        return output_string


def smart_output_error(file):
    """

    :param file: a HTCondor .err file
    :return: the content of the given file as a string
    """

    # Todo:
    # - errors from htcondor are more important (std.err output)
    # - are there errors ? true or false -> maybe print those in any kind of fromat
    # - maybe check for file size !!!
    # - is the file size the same ? what is normal / different errors (feature -> for  -> later)

    output_string = ""
    try:
        error_content = read_condor_error(file)
        for line in error_content.split("\n"):
            if "err" in line.lower() and not ignore_errors:
                output_string += red + line + back_to_default + "\n"
            elif "warn" in line.lower() and show_warnings:
                output_string += yellow + line + back_to_default + "\n"

    except NameError as err:
        logging.exception(err)
        print("The smart_output_error method requires a "+std_err+" file as parameter")
    except FileNotFoundError:
        relevant = file.split("/")[-2:]
        match = re.match(r".*?([0-9]{3,}_[0-9]+)"+std_err, relevant[1])
        print(yellow + "There is no related {0} file: {1} in the directory:{2}\n'{3}'\n"
              " with the prefix: {4}{5}"
              .format(std_err, relevant[1], cyan, os.path.abspath(relevant[0]), match[1], back_to_default))
    except TypeError as err:
        logging.exception(err)
        print(red+str(err)+back_to_default)
    finally:
        return output_string


def smart_output_output(file):
    """
    Todo: filter the output ?
    :param file: a HTCondor .out file
    :return: the content of that file as a string
    """

    output_string = ""
    try:
        output_string = read_condor_output(file)
    except NameError as err:
        logging.exception(err)
        print("The smart_output_output method requires a "+std_out+" file as parameter")
    except FileNotFoundError:
        relevant = file.split("/")[-2:]
        match = re.match(r".*?([0-9]{3,}_[0-9]+)"+std_out, relevant[1])
        print(yellow + "There is no related {0} file: {1} in the directory:{2}\n'{3}'\n"
                       " with the prefix: {4}{5}"
              .format(std_out, relevant[1], cyan, os.path.abspath(relevant[0]), match[1], back_to_default))

    finally:
        return output_string


def smart_manage_all(job_spec_id):
    """
    Combine all informations, that the user wants for a given job_spec_id like 398_31.
    -the first layer represents the HTCondor .log file
    -the second layer represents the HTCondor .err file
    -the third layer represents the HTCondor .out file

    information will be put together regarding the global booleans set by the user.
    job_spec_id, is the ClusterID_ProcessID of a job executed by HTCondor like job_4323_21 or 231_0

    :param job_spec_id: file name without endling like job4323_1, job4323_1.<err|out|log> will cut the end off
    :return: a string that combines HTCondor log/err and out files and returns it
    """
    # error handling, if a file name like 398_0.log was given,
    if job_spec_id[-4:].__eq__(std_log):
        job_spec_id = job_spec_id[:-4]

    try:

        output_string = smart_output_logs(job_spec_id + std_log)  # normal smart_output of log files

        if not ignore_errors:  # ignore errors ?
            output_string += smart_output_error(job_spec_id + std_err)

        if show_output:  # show output content ?
            output_string += smart_output_output(job_spec_id + std_out)
    except Exception as err:
        logging.exception(err)
        print(red+str(err)+back_to_default)
        exit(0)
    else:
        return output_string


# Todo: params should affect output and error files
# Todo: use the manage_all function
def read_through_logs_dir(directory):
    """
    Runs through the given directory and return all logs related content
    via the smart_output_logs methods

    :param directory: a directory were the *log/err/out* files should be stored

    :return: an output string, that returns all outputs
    """
    # Todo:
    path = os.getcwd()  # current working directory , should be condor job summariser script
    logs_path = path + "/" + directory

    if os.path.isdir(logs_path):
        working_path = logs_path
    elif os.path.isdir(directory):
        working_path = directory
    else:
        raise NameError("The given directory is either no directory or the path was wrong")

    output_string = ""
    # list are better to separate corresponding files
    list_of_logs = list()
    list_of_errors = list()
    list_of_outputs = list()
    # run through all files and separate the files into log/error and output files
    for file in os.listdir(working_path):
        if file.endswith(std_log):
            list_of_logs.append(file)
        elif file.endswith(std_err):
            list_of_errors.append(file)
        elif file.endswith(std_out):
            list_of_outputs.append(file)

    list_of_logs.sort()
    # Todo: more params, that will make the output more dynamically for:
    # Errors, Warnings, output, kind of errors, job_descriptions, etc.
    for file in list_of_logs:
        job_id = file[:-4]
        file_path = directory + "/" + job_id

        output_string += smart_manage_all(file_path)
        # separate logs if file is not the last occurring file in the files list
        if not file == list_of_logs[-1] or not directory == files[-1]:
            output_string += "\n" + border_str + "\n"

    return output_string


def summarise_given_logs():
    global files
    output_string = ""
    current_path = os.getcwd()
    # go through all given logs and check for each if it is a directory or file and if std_log was missing or not
    for file in files:

        # for the * operation it should skip std_err and std_out files
        if file.endswith(std_err) or file.endswith(std_out):
            continue

        # check if file is a directory and run through the whole directory
        if os.path.isdir(file) or os.path.isdir(current_path + "/" + file):
            output_string += read_through_logs_dir(file)
        # else check if file is a valid file
        elif os.path.isfile(file) or os.path.isfile(current_path + "/" + file):
            output_string += smart_manage_all(file)

        # if that did not work try std_log at the end of that file
        elif not file.endswith(std_log):
            new_path = file + std_log
            # is this now a valid file ?
            if os.path.isfile(new_path) or os.path.isfile(current_path + "/" + new_path):
                output_string += smart_manage_all(new_path)
            # no file or directory found, even after manipulating the string
            else:
                logging.error("No such file with that name or prefix: {0}".format(file))
                output_string += red+"No such file with that name or prefix: {0}".format(file)+back_to_default
        # The given .log file was not found
        else:
            output_string += red + "No such file: {0}".format(file) + back_to_default
            logging.error("No such file: {0}".format(file))

        # don't change output if csv style is wanted
        if resources_to_csv or job_to_csv:
            pass
        # because read_through_dir is already separating and after the last occurring file
        # no separation is needed
        elif not os.path.isdir(file) and not os.path.isdir(current_path + "/" + file) and not file == files[-1]:
            output_string += "\n" + border_str + "\n"  # if empty it still contains a newline

    if output_string == "":
        output_string = "None"

    return output_string


# search for config file ( UNIX BASED )
# Todo: Test
def load_config(file):
    """

    Reads config file and changes global parameter by its configuration

    :param file:
    :return: False if not found, True if found and
    """

    script_name = sys.argv[0][:-3]  # scriptname without .py
    config = configparser.ConfigParser()
    # search for the given file, first directly, then in /etc and then in ~/.config/HTCompact/
    try:
        if os.path.isfile(file):
            logging.debug("Load config file from htcondor-summariser-script project: {0}".format(file))
            config.read(file)
        # try to find config file in /etc
        elif os.path.isfile("/etc/{0}".format(file)):
            logging.debug("Load config from: /etc/{0}".format(file))
            config.read("/etc/{0}.conf".format(script_name))
        # try to find config file in ~/.config/script_name/
        elif os.path.isfile("~/.config/{0}/{1}".format(script_name, file)):
            logging.debug("Load config from: ~/.config/{0}/{1}".format(script_name, file))
        else:
            logging.debug("No config file found")
            return False

    # File has no readable format for the configparser, probably because it's not a config file
    except configparser.MissingSectionHeaderError:
        return False

    try:
        # all sections in the config file
        sections = config.sections()

        # now try filter the config file for all available parameters

        # all documents like files, etc.
        if 'documents' in sections:
            global files

            if 'files' in config['documents']:
                files = config['documents']['files'].split(" ")
                logging.debug('Changed document files to {0}'.format(files))

        # all formats like the table format
        if 'formats' in sections:
            global table_format
            if 'table_format' in config['formats']:
                table_format = config['formats']['table_format']
                logging.debug("Changed default table_format to: {0}".format(table_format))

        # all basic HTCondor file endings like .log, .err, .out
        if 'htc-files' in sections:
            global std_log, std_err, std_out

            if 'stdlog' in config['htc-files']:
                std_log = config['htc-files']['stdlog']
                logging.debug("Changed default for HTCondor .log files to: {0}".format(std_log))

            if 'stderr' in config['htc-files']:
                std_err = config['htc-files']['stderr']
                logging.debug("Changed default for HTCondor .err files to: {0}".format(std_err))

            if 'stdout' in config['htc-files']:
                std_out = config['htc-files']['stdout']
                logging.debug("Changed default for HTCondor .out files to: {0}".format(std_out))

        # if show variables are set for further output
        if 'show-more' in sections:
            global show_output, show_warnings, show_allocated_res  # sources to show

            if 'show_output' in config['show-more']:
                show_output = True if config['show-more']['show_output'].lower() == "true" else False
                logging.debug("Changed default show_output to: {0}".format(show_output))

            if 'show_warnings' in config['show-more']:
                show_warnings = True if config['show-more']['show_warnings'].lower() == "true" else False
                logging.debug("Changed default show_warnings to: {0}".format(show_warnings))

            if 'show_allocated_resources' in config['show-more']:
                show_allocated_res = True if config['show-more']['show_allocated_resources'].lower() == "true"\
                                     else False
                logging.debug("Changed default show_allocated_res to: {0}".format(show_allocated_res))

        # what information should to be ignored
        if 'ignore' in sections:
            global ignore_errors, ignore_resources  # sources to ignore

            if 'ignore_errors' in config['ignore']:
                ignore_errors = True if config['ignore']['ignore_errors'].lower() == "true" else False
                logging.debug("Changed default ignore_errors to: {0}".format(ignore_errors))
            if 'ignore_resources' in config['ignore']:
                ignore_resources = True if config['ignore']['ignore_resources'].lower() == "true" else False
                logging.debug("Changed default ignore_resources to: {0}".format(ignore_resources))

        # Todo: thresholds
        if 'thresholds' in sections:
            pass

        if 'csv' in sections:
            global resources_to_csv, job_to_csv, indexing
            if 'resources_to_csv' in config['csv']:
                resources_to_csv = True if config['csv']['resources_to_csv'].lower() == "true" else False
                logging.debug("Changed default resources_to_csv to: {0}".format(resources_to_csv))
            if 'job_to_csv' in config['csv']:
                job_to_csv = True if config['csv']['job_to_csv'].lower() == "true" else False
                logging.debug("Changed default job_to_csv to: {0}".format(job_to_csv))
            if 'indexing' in config['csv']:
                indexing = True if config['csv']['indexing'].lower() == "true" else False
                logging.debug("Changed default indexing to: {0}".format(indexing))

        # Todo: reverse DNS-Lookup etc.
        if 'features' in sections:
            global reverse_dns_lookup  # extra parameters

        return True

    except KeyError as err:
        logging.exception(err)
        return False


def main():
    """
    This is the main function, which searchs first for a given config file.
    After that, given parameters in the terminal will be interpreted, so they have a higher priority

    Then it will summarise all given log files together and print the output

    :return:
    """

    found_config = False

    # check if a valid config file is underneeth the given files
    if len(sys.argv) > 1:
        for file in sys.argv[1:]:
            if load_config(file):
                found_config = True
                sys.argv.remove(file)
                logging.debug("Removed {0} from arguments".format(file))

    # else try to find the default setup.conf file
    if not found_config:
        load_config("setup.conf")

    manage_params()  # manage the given variables and overwrite the config set variables

    output_string = summarise_given_logs()  # print out all given files if possible

    # if for csv-format just one type if given, add the labels as the first line
    if resources_to_csv and not job_to_csv:
        temp_str = "Recources," if indexing else ""
        temp_str += "Usage,Requested"
        temp_str += ",Allocated" if show_allocated_res else ""
        output_string = temp_str + "\n" + output_string
    elif job_to_csv and not resources_to_csv:
        temp_str = "Description," if indexing else ""
        temp_str += "Values"
        output_string = temp_str +"\n"+ output_string

    print(output_string)  # write it to the console


logging.debug("-------Start of HTCompact scipt-------")
main()
logging.debug("-------End of HTCompact script-------")
