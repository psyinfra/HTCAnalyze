#
# from htcanalyze.time_manager import TimeManager, calc_avg_on_times
#
# def test_gen_time_dict():
#
#     strp_format = "%Y-%m-%dT%H:%M:%S"
#     strf_format = "%m/%d %H:%M:%S"
#     today = datetime.datetime.now()
#     today = today.replace(microsecond=0)
#
#     submission = "2019-6-23T22:25:25"
#     execution = "2019-6-24T06:32:25"
#     termination = "2020-01-13T6:5:5"
#
#     sub_date = datetime.datetime.strptime(submission, strp_format)
#     exec_date = datetime.datetime.strptime(execution, strp_format)
#     term_date = datetime.datetime.strptime(termination, strp_format)
#
#     # test all None
#     time_dict = gen_time_dict()
#     assert time_dict is None
#
#     # test only submission date given
#     waiting_time = today - sub_date
#     time_dict = gen_time_dict(sub_date)
#     assert time_dict['Dates and times'] == ['Submission date', 'Waiting time']
#     assert time_dict['Values'][0] == sub_date.strftime(strf_format)
#     assert time_dict['Values'][1] == waiting_time
#
#     # test only execution date given
#     time_dict = gen_time_dict(execution_date=exec_date)
#     assert time_dict['Dates and times'] == ['Execution date']
#     assert time_dict['Values'][0] == exec_date.strftime(strf_format)
#
#     # test only termination date given
#     time_dict = gen_time_dict(termination_date=term_date)
#     assert time_dict['Dates and times'] == ['Termination date']
#     assert time_dict['Values'][0] == term_date.strftime(strf_format)
#
#     # test only submission and execution date given
#     time_dict = gen_time_dict(sub_date, exec_date)
#     assert time_dict['Dates and times'] == ['Submission date',
#                                             'Execution date',
#                                             'Waiting time',
#                                             'Execution runtime']
#     waiting_time = exec_date - sub_date
#     execution_runtime = today - exec_date
#     assert time_dict['Values'][0] == sub_date.strftime(strf_format)
#     assert time_dict['Values'][1] == exec_date.strftime(strf_format)
#     assert time_dict['Values'][2] == waiting_time
#     assert time_dict['Values'][3] == execution_runtime
#
#     # test only submission and termination date given
#     time_dict = gen_time_dict(submission_date=sub_date,
#                               termination_date=term_date)
#     assert time_dict['Dates and times'] == ['Submission date',
#                                             'Termination date',
#                                             'Total runtime']
#     total_runtime = term_date - sub_date
#     assert time_dict['Values'][0] == sub_date.strftime(strf_format)
#     assert time_dict['Values'][1] == term_date.strftime(strf_format)
#     assert time_dict['Values'][2] == total_runtime
#
#     # test only execution and termination date given
#     time_dict = gen_time_dict(submission_date=None,
#                               execution_date=exec_date,
#                               termination_date=term_date)
#     execution_runtime = term_date - exec_date
#     assert time_dict['Dates and times'] == ['Execution date',
#                                             'Termination date',
#                                             'Execution runtime']
#     assert time_dict['Values'][0] == exec_date.strftime(strf_format)
#     assert time_dict['Values'][1] == term_date.strftime(strf_format)
#     assert time_dict['Values'][2] == execution_runtime
#
#     # test all given
#     time_dict = gen_time_dict(submission_date=sub_date,
#                               execution_date=exec_date,
#                               termination_date=term_date)
#     assert time_dict['Dates and times'] == ['Submission date',
#                                             'Execution date',
#                                             'Termination date',
#                                             'Waiting time',
#                                             'Execution runtime',
#                                             'Total runtime']
#     waiting_time = exec_date - sub_date
#     execution_runtime = term_date - exec_date
#     total_runtime = term_date - sub_date
#     assert time_dict['Values'][0] == sub_date.strftime(strf_format)
#     assert time_dict['Values'][1] == exec_date.strftime(strf_format)
#     assert time_dict['Values'][2] == term_date.strftime(strf_format)
#     assert time_dict['Values'][3] == waiting_time
#     assert time_dict['Values'][4] == execution_runtime
#     assert time_dict['Values'][5] == total_runtime
