import re
import sys
import os
import getopt
import datetime

"""

Version 1.1
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
filter_for_error = ""

# variables for given parameters
show_output = False
show_warnings = False
ignore_all = False
ignore_errors = False
ignore_resources = False

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


# Todos:
# Todo: did a lot of test, but it needs more
# Todo: background colors etc. for terminal usage
# Todo: filter erros better, less priority
# Todo: realise the further specs on: https://jugit.fz-juelich.de/inm7/infrastructure/scripts/-/issues/1
# Todo: make global variable for err/log/out files, should be given by user if not in default form
# Todo: make the ressources visiable in a grid
# a redirection in the terminal via > should ignore escape sequences


# may not be needed in future but will be used for now
def ignore_spaces_in_arguments(args):
    """
        I want to make it easier for the user to insert many files at once are spaces between arguments.

        I want that this is possible: python3 do_the_magic.py -f file1 file2 file3 ... -otheropts
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
    global show_output, show_warnings  # show more information variables
    global ignore_all, ignore_errors, ignore_resources  # ignore information variables

    try:
        better_args = ignore_spaces_in_arguments(sys.argv[1:])

        # interpret the first arguments after sys.argv[0] as files/directories
        if not better_args[0].startswith("-"):
            files = better_args[0].split()
            better_args = better_args[1:]  # remove them from opts

        opts, args = getopt.getopt(better_args, "h",
                                   ["help", "std-log=", "std-error=", "std-out=",
                                    "show-output", "show-warnings",
                                    "ignore-all", "ignore-errors", "ignore-resources"])
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

            # all variables to ignore unwanted information
            elif opt.__eq__("--ignore-all"):
                ignore_all = True
            elif opt.__eq__("--ignore-errors"):
                ignore_errors = True
            elif opt.__eq__("--ignore-resources"):
                ignore_resources = True

            else:
                print(help_me())
                exit(0)

        # if output gets redirected with >, ignore escape sequences
        if not sys.stdout.isatty():
            global red, green, yellow, cyan, back_to_default
            red = ""
            green = ""
            yellow = ""
            cyan = ""
            back_to_default = ""

    except (getopt.GetoptError or UnboundLocalError or NameError) as err:
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


# Todo: gpu usage
def smart_output_logs(file):
    """
    reads a given HTCondor .log file with the read_condor_logs() function

    :param file:    a HTCondor .log file

    :return:        (output_string)
                    an output string that shows information like:
                    Job executing on host: <host>
                    Job runtime: <HH:MM:SS>
                    Max RAM used: <memory_usage> MB vs.requested: <memory_request> MB
                    Max Disk used: <disk_usage> KB vs.requested: <disk_request> KB
                    average CPU usage: <cpu_usage> vs.requested: <cpu_request>
    """
    try:
        job_events, job_information = read_condor_logs(file)
        global border_str

        output_string = green+"The job procedure of : " + file + back_to_default + "\n"
        border_str = "-" * len(output_string) + "\n"
        output_string += border_str

        if job_events[-1][0].__eq__("005"):  # if the last job event is : Job terminated

            output_string += job_events[1][4][1:] + ": " + job_events[1][5][2:15] + "\n"

            # calculate the runtime for the job
            submitted_date = datetime.datetime.strptime(job_events[0][2] + " " + job_events[0][3], "%m/%d %H:%M:%S")
            terminating_date = datetime.datetime.strptime(job_events[-1][2] + " " + job_events[-1][3], "%m/%d %H:%M:%S")
            difference = terminating_date - submitted_date  # calculation of the time difference

            output_string += "Job runtime: " + str(difference) + "\n"  # job runtime

            if not ignore_resources:  # ignore resources ?

                relevant_str = "\n".join(job_information[-1])  # job information of the last job (Job terminated)

                if True:  # just for readability
                    # remove unnecessary lines
                    lines = relevant_str.splitlines()
                    while not lines[0].startswith("\tPartitionable"):
                        lines.remove(lines[0])

                    lines.remove(lines[0])
                    partitionable_resources = lines
                    # done, partitionable_resources contain now only information about used resources

                match = re.match(r"\t *Cpus *: *([0-9]?(?:\.[0-9]{2})?) *([0-9]+) *([0-9]+)", partitionable_resources[0])
                if match:
                    cpu_usage, cpu_request, cpu_allocated = match[1], match[2], match[3]
                match = re.match(r"\t *Disk \(KB\) *: *([0-9]+) *([0-9]+) *([0-9]+)", partitionable_resources[1])
                if match:
                    disk_usage, disk_request, disk_allocated = match[1], match[2], match[3]
                match = re.match(r"\t *Memory \(MB\)  *: *([0-9]+) *([0-9]+) *([0-9]+)", partitionable_resources[2])
                if match:
                    memory_usage, memory_request, memory_allocated = match[1], match[2], match[3]

                # print(cpu_usage, cpu_request, cpu_allocated)
                # print(disk_usage, disk_request, disk_allocated)
                # print(memory_usage, memory_request, memory_allocated)

                # Error handling: change empty value of cpu_usage to NaN
                if cpu_usage == "":
                    cpu_usage = "NaN"

                # fill the string with important information
                output_string += "Max RAM used:      " + memory_usage + " MB vs. requested: " + memory_request + " MB\n"
                output_string += "Max Disk used:     " + disk_usage + " KB vs. requested: " + disk_request + " KB\n"
                output_string += "average CPU usage: " + cpu_usage + " vs. requested: " + cpu_request + "\n"

        # Todo: more information, maybe why ?
        elif job_events[-1][0].__eq__("009"):  # job aborted

            # job_event description, which is "Job was aborted by the user" and the user filter
            output_string += job_events[-1][4][1:] + ": " + ((job_information[-1][0]).split(" ")[-1])[:-1]+"\n"

    except NameError:
        print("The smart_output_logs method requires a "+std_log+" file as parameter")
    except FileNotFoundError as err:
        print(red+str(err)+back_to_default)
    else:
        return output_string


def smart_output_error(file):
    """

    :param file: a HTCondor .err file
    :return: the content of the given file as a string
    """

    output_string = ""
    try:
        error_content = read_condor_error(file)
        for line in error_content.split("\n"):
            if "err" in line.lower() and not ignore_errors:
                output_string += red + line + back_to_default + "\n"
            elif "warn" in line.lower() and show_warnings:
                output_string += yellow + line + back_to_default + "\n"

    except NameError:
        print("The smart_output_error method requires a "+std_err+" file as parameter")
    except FileNotFoundError:
        relevant = file.split("/")[-2:]
        match = re.match(r".*?([0-9]{3,}_[0-9]+)"+std_err, relevant[1])
        print(yellow + "There is no related {0} file: {1} in the directory:{2}\n'{3}'\n"
              " with the prefix: {4}{5}"
              .format(std_err, relevant[1], cyan, os.path.abspath(relevant[0]), match[1], back_to_default))
    except TypeError as err:
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
    except NameError:
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

        if ignore_all:  # ignore errors and output ?
            return output_string

        output_string += smart_output_error(job_spec_id + std_err)

        if show_output:  # show output content ?
            output_string += smart_output_output(job_spec_id + std_out)
    except Exception as error:
        print(red+str(error)+back_to_default)
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
        output_string += border_str

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
                output_string += red+"No such file or directory: "+file+back_to_default
        # No file found
        else:
            output_string += red + "No such file: " + file + back_to_default
        output_string += border_str  # if empty it still contains a newline

    if output_string == "":
        output_string = "No"

    return output_string


def main():
    manage_params()  # check the given variables and check the global parameters
    output_string = summarise_given_logs()  # print out all given files if possible
    print(output_string)


main()
