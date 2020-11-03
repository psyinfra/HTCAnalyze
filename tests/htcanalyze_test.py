
import datetime
import pytest
from htcanalyze.htcanalyze import HTCAnalyze, sort_dict_by_col


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
    assert htcan.rdns_cache == {}
    assert htcan.rdns_lookup is False
    assert htcan.tolerated_usage == 0.1
    assert htcan.bad_usage == 0.25


def test_log_to_dict(htcan):
    """Tests the log_to_dict function of HTCAnalyze class.

    Only the following files are tested:

    - tests/test_logs/valid_logs/normal_log.log
    - tests/test_logs/valid_logs/aborted_with_errors.log

    :param htcan:
    :return:
    """
    file = "tests/test_logs/valid_logs/normal_log.log"
    job_events_dict, resources, time_manager, \
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

    assert resources[0].description == "CPU"
    assert resources[0].usage == 0.11
    assert resources[0].requested == 1
    assert resources[0].allocated == 1

    assert resources[1].description == "Disk (KB)"
    assert resources[1].usage == 4
    assert resources[1].requested == 20200960
    assert resources[1].allocated == 22312484

    assert resources[2].description == "Memory (MB)"
    assert resources[2].usage == 922
    assert resources[2].requested == 20480
    assert resources[2].allocated == 20480

    assert time_manager.create_time_dict() == {
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
    job_events_dict, resources, time_manager, \
        ram_history_dict, error_dict = htcan.log_to_dict(file)

    assert job_events_dict == {
        'Execution details': ['Process was', 'Submitted from', 'Executing on'],
        'Values': ['[red]Aborted[/red]', '10.0.8.10', '10.0.9.1']}

    assert resources == []

    assert time_manager.create_time_dict() == {
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
