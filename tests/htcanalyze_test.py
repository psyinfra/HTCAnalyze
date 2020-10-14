
import datetime
import pytest
import numpy as np
from htcanalyze.htcanalyze import HTCAnalyze, gen_time_dict, sort_dict_by_col


def test_gen_time_dict():

    strp_format = "%Y-%m-%dT%H:%M:%S"
    strf_format = "%m/%d %H:%M:%S"
    today = datetime.datetime.now()
    today = today.replace(microsecond=0)

    submission = "2019-6-23T22:25:25"
    execution = "2019-6-24T06:32:25"
    termination = "2020-01-13T6:5:5"

    sub_date = datetime.datetime.strptime(submission, strp_format)
    exec_date = datetime.datetime.strptime(execution, strp_format)
    term_date = datetime.datetime.strptime(termination, strp_format)

    # test all None
    time_dict = gen_time_dict()
    assert time_dict['Dates and times'] == []
    assert time_dict['Values'] == []

    # test only submission date given
    waiting_time = today - sub_date
    time_dict = gen_time_dict(sub_date)
    assert time_dict['Dates and times'] == ['Submission date', 'Waiting time']
    assert time_dict['Values'][0] == sub_date.strftime(strf_format)
    assert time_dict['Values'][1] == waiting_time

    # test only execution date given
    time_dict = gen_time_dict(execution_date=exec_date)
    assert time_dict['Dates and times'] == ['Execution date']
    assert time_dict['Values'][0] == exec_date.strftime(strf_format)

    # test only termination date given
    time_dict = gen_time_dict(termination_date=term_date)
    assert time_dict['Dates and times'] == ['Termination date']
    assert time_dict['Values'][0] == term_date.strftime(strf_format)

    # test only submission and execution date given
    time_dict = gen_time_dict(sub_date, exec_date)
    assert time_dict['Dates and times'] == ['Submission date',
                                            'Execution date',
                                            'Waiting time',
                                            'Execution runtime']
    waiting_time = exec_date - sub_date
    execution_runtime = today - exec_date
    assert time_dict['Values'][0] == sub_date.strftime(strf_format)
    assert time_dict['Values'][1] == exec_date.strftime(strf_format)
    assert time_dict['Values'][2] == waiting_time
    assert time_dict['Values'][3] == execution_runtime

    # test only submission and termination date given
    time_dict = gen_time_dict(submission_date=sub_date,
                              termination_date=term_date)
    assert time_dict['Dates and times'] == ['Submission date',
                                            'Termination date',
                                            'Total runtime']
    total_runtime = term_date - sub_date
    assert time_dict['Values'][0] == sub_date.strftime(strf_format)
    assert time_dict['Values'][1] == term_date.strftime(strf_format)
    assert time_dict['Values'][2] == total_runtime

    # test only execution and termination date given
    time_dict = gen_time_dict(submission_date=None,
                              execution_date=exec_date,
                              termination_date=term_date)
    execution_runtime = term_date - exec_date
    assert time_dict['Dates and times'] == ['Execution date',
                                            'Termination date',
                                            'Execution runtime']
    assert time_dict['Values'][0] == exec_date.strftime(strf_format)
    assert time_dict['Values'][1] == term_date.strftime(strf_format)
    assert time_dict['Values'][2] == execution_runtime

    # test all given
    time_dict = gen_time_dict(submission_date=sub_date,
                              execution_date=exec_date,
                              termination_date=term_date)
    assert time_dict['Dates and times'] == ['Submission date',
                                            'Execution date',
                                            'Termination date',
                                            'Waiting time',
                                            'Execution runtime',
                                            'Total runtime']
    waiting_time = exec_date - sub_date
    execution_runtime = term_date - exec_date
    total_runtime = term_date - sub_date
    assert time_dict['Values'][0] == sub_date.strftime(strf_format)
    assert time_dict['Values'][1] == exec_date.strftime(strf_format)
    assert time_dict['Values'][2] == term_date.strftime(strf_format)
    assert time_dict['Values'][3] == waiting_time
    assert time_dict['Values'][4] == execution_runtime
    assert time_dict['Values'][5] == total_runtime


def test_sort_dict_by_column():
    test_dict = {
        "Key1": ["Hello", "It's", "Me", "I", "Was", "Wondering"],
        "Key2": [1, 3, 6, 5, 2, 4],
        "Key3": ["a", "b", "d", "c", "e", "f"]
    }
    sorted_by_key1 = {'Key1': ['Hello', 'I', "It's", 'Me', 'Was', 'Wondering'],
                      'Key2': [1, 5, 3, 6, 2, 4],
                      'Key3': ['a', 'c', 'b', 'd', 'e', 'f']}
    sorted_by_key2 = {'Key1': ['Hello', 'Was', "It's", 'Wondering', 'I', 'Me'],
                      'Key2': [1, 2, 3, 4, 5, 6],
                      'Key3': ['a', 'e', 'b', 'f', 'c', 'd']}
    sorted_by_key3 = {'Key1': ['Hello', "It's", 'I', 'Me', 'Was', 'Wondering'],
                      'Key2': [1, 3, 5, 6, 2, 4],
                      'Key3': ['a', 'b', 'c', 'd', 'e', 'f']}

    sorted_dict = sort_dict_by_col(test_dict, "Key1", reverse=False)
    assert sorted_dict == sorted_by_key1
    sorted_dict = sort_dict_by_col(test_dict, "Key2", reverse=False)
    assert sorted_dict == sorted_by_key2
    sorted_dict = sort_dict_by_col(test_dict, "Key3", reverse=False)
    assert sorted_dict == sorted_by_key3

    sorted_by_key1_reversed = {
        'Key1': ['Wondering', 'Was', 'Me', "It's", 'I', 'Hello'],
        'Key2': [4, 2, 6, 3, 5, 1],
        'Key3': ['f', 'e', 'd', 'b', 'c', 'a']}
    sorted_by_key2_reversed = {
        'Key1': ['Me', 'I', 'Wondering', "It's", 'Was', 'Hello'],
        'Key2': [6, 5, 4, 3, 2, 1],
        'Key3': ['d', 'c', 'f', 'b', 'e', 'a']}
    sorted_by_key3_reversed = {
        'Key1': ['Wondering', 'Was', 'Me', 'I', "It's", 'Hello'],
        'Key2': [4, 2, 6, 5, 3, 1],
        'Key3': ['f', 'e', 'd', 'c', 'b', 'a']}

    sorted_dict = sort_dict_by_col(test_dict, "Key1")

    assert sorted_dict == sorted_by_key1_reversed
    sorted_dict = sort_dict_by_col(test_dict, "Key2")
    assert sorted_dict == sorted_by_key2_reversed
    sorted_dict = sort_dict_by_col(test_dict, "Key3")
    assert sorted_dict == sorted_by_key3_reversed


@pytest.fixture(scope="module")
def htcan():
    htcan = HTCAnalyze()
    return htcan


def test_HTCAnalyze_init(htcan):
    assert htcan.ext_log == ""
    assert htcan.ext_err == ".err"
    assert htcan.ext_out == ".out"
    assert htcan.show_list == []
    assert htcan.store_dns_lookups == {}
    assert htcan.reverse_dns_lookup is False
    assert htcan.tolerated_usage == 0.1
    assert htcan.bad_usage == 0.25


def test_manage_thresholds(htcan):
    htcan.tolerated_usage = 0.1
    htcan.bad_usage = 0.25
    res_dict = {
        "Resources": ["Cpu", "Disk", "Memory"],
        "Usage": [0.23, 3000, 4051],
        "Requested": [1, 2700, 4500],
        "Allocated": [1, 6000, 6000]
    }
    expected_dict = {'Resources': ['Cpu', 'Disk', 'Memory'],
                     'Usage': ['[red]0.23[/red]',
                               '[yellow]3000[/yellow]',
                               '[green]4051[/green]'],
                     'Requested': [1, 2700, 4500],
                     'Allocated': [1, 6000, 6000]}
    managed_res = htcan.manage_thresholds(res_dict)
    assert managed_res == expected_dict


def test_log_to_dict(htcan):
    """Tests the log_to_dict function of HTCAnalyze class.

    Only the following files are tested:

    - tests/test_logs/valid_logs/normal_log.log
    - tests/test_logs/valid_logs/aborted_with_errors.log

    :param htcan:
    :return:
    """
    file = "tests/test_logs/valid_logs/normal_log.log"
    job_events_dict, res_dict, time_dict, \
        ram_history_dict, error_dict = htcan.log_to_dict(file)

    assert job_events_dict == {
        'Execution details': ['Termination State',
                              'Submitted from',
                              'Executing on',
                              'Return Value'],
        'Values': ['[green]Normal[/green]',
                   '10.0.8.10',
                   '10.0.9.201',
                   1]}

    assert list(res_dict.keys()) == [
        "Resources", "Usage", "Requested", "Allocated"]
    assert res_dict['Resources'] == ["Cpu", "Disk", "Memory"]
    assert np.array_equal(res_dict['Usage'],
                          [1.10e-01, 4.00e+00, 9.22e+02]) is True
    assert np.array_equal(res_dict['Requested'],
                          [1.000000e+00, 2.020096e+07, 2.048000e+04]) is True
    assert np.array_equal(res_dict['Allocated'],
                          [1.0000e+00, 2.2312484e+07, 2.0480000e+04]) is True

    assert time_dict == {
        'Dates and times': ['Submission date',
                            'Execution date',
                            'Termination date',
                            'Waiting time',
                            'Execution runtime',
                            'Total runtime'],
        'Values': ['07/11 20:39:51',
                   '07/11 20:39:54',
                   '07/11 20:45:50',
                   datetime.timedelta(seconds=3),
                   datetime.timedelta(seconds=356),
                   datetime.timedelta(seconds=359)]}

    assert ram_history_dict == {
        'Dates': [datetime.datetime(2020, 7, 11, 20, 40, 3),
                  datetime.datetime(2020, 7, 11, 20, 45, 4)],
        'Image size updates': [448, 1052936],
        'Memory usages': [1, 922],
        'Resident Set Sizes': [448, 943244]}

    assert error_dict == {}

    file = "tests/test_logs/valid_logs/aborted_with_errors.log"
    job_events_dict, res_dict, time_dict, \
        ram_history_dict, error_dict = htcan.log_to_dict(file)

    assert job_events_dict == {
        'Execution details': ['Process was', 'Submitted from', 'Executing on'],
        'Values': ['[red]Aborted[/red]', '10.0.8.10', '10.0.9.1']}

    assert res_dict == {}

    assert time_dict == {
        'Dates and times': ['Submission date',
                            'Execution date',
                            'Termination date',
                            'Waiting time',
                            'Execution runtime',
                            'Total runtime'],
        'Values': ['02/11 09:45:05',
                   '02/11 12:29:18',
                   '02/25 09:29:26',
                   datetime.timedelta(seconds=9853),
                   datetime.timedelta(days=13, seconds=75608),
                   datetime.timedelta(days=13, seconds=85461)]}

    assert ram_history_dict == {
        'Dates': [datetime.datetime(2020, 2, 11, 12, 29, 26)],
        'Image size updates': [28644],
        'Memory usages': [28],
        'Resident Set Sizes': [28644]}

    assert error_dict == {
        'Event Number': [7, 12, 9],
        'Time': ['02/11 12:31:27', '02/11 12:31:27', '02/25 09:29:26'],
        'Error': ['SHADOW_EXCEPTION', 'JOB_HELD', 'Aborted'],
        'Reason': ['Error from slot1_4@cpu1.htc.inm7.de: '
                   'Job has encountered an out-of-memory event.',
                   'Error from slot1_4@cpu1.htc.inm7.de: '
                   'Job has encountered an out-of-memory event.',
                   'via condor_rm (by user tkadelka)']}


def test_reverse_dns_lookup(htcan):
    htcan.gethostbyaddr("172.217.0.0")
    assert htcan.store_dns_lookups["172.217.0.0"] == "ord38s04-in-f0.1e100.net"
    htcan.gethostbyaddr("NoIP")
    assert htcan.store_dns_lookups["NoIP"] == "NoIP"
