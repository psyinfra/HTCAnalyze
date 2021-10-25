
from datetime import datetime, timedelta
from htcanalyze.log_analyzer.condor_log.time_manager import TimeManager
from htcanalyze.globals import STRP_FORMAT

submission = "2020-3-16T22:25:25"
execution = "2020-6-24T06:32:25"
termination = "2020-01-13T6:5:5"

today = datetime.now()
today = today.replace(microsecond=0)

sub_date = datetime.strptime(submission, STRP_FORMAT)
exec_date = datetime.strptime(execution, STRP_FORMAT)
term_date = datetime.strptime(termination, STRP_FORMAT)


def test_only_sub_date():
    # test only submission date given
    time_manager = TimeManager(sub_date, None, None)
    waiting_time = today - sub_date
    assert time_manager.submission_date == sub_date
    assert time_manager.execution_date is None
    assert time_manager.termination_date is None
    assert time_manager.waiting_time == waiting_time
    assert time_manager.execution_time == timedelta()
    assert time_manager.total_runtime == waiting_time


def test_only_exec_date():
    # test only execution date given
    time_manager = TimeManager(None, exec_date, None)
    exec_time = today-exec_date
    assert time_manager.submission_date is None
    assert time_manager.execution_date == exec_date
    assert time_manager.termination_date is None
    assert time_manager.waiting_time == timedelta()
    assert time_manager.execution_time == exec_time
    assert time_manager.total_runtime == exec_time


def test_only_term_date():
    # test only termination date given
    time_manager = TimeManager(None, None, term_date)
    assert time_manager.submission_date is None
    assert time_manager.execution_date is None
    assert time_manager.termination_date == term_date
    assert time_manager.waiting_time == timedelta()
    assert time_manager.execution_time == timedelta()
    assert time_manager.total_runtime == timedelta()


def test_sub_and_exec_date():
    # test only submission and execution date given
    time_manager = TimeManager(sub_date, exec_date, None)
    assert time_manager.submission_date == sub_date
    assert time_manager.execution_date == exec_date
    assert time_manager.termination_date is None
    waiting_time = exec_date - sub_date
    execution_runtime = today - exec_date
    total_runtime = today - sub_date
    assert time_manager.waiting_time == waiting_time
    assert time_manager.execution_time == execution_runtime
    assert time_manager.total_runtime == total_runtime


def test_sub_and_term_date():
    # test only submission and termination date given
    time_manager = TimeManager(sub_date, None, term_date)
    fixed_sub_date = TimeManager.decrease_year(sub_date)
    assert time_manager.submission_date == fixed_sub_date
    assert time_manager.execution_date is None
    assert time_manager.termination_date == term_date
    waiting_time = term_date - fixed_sub_date
    assert time_manager.waiting_time == waiting_time
    assert time_manager.execution_time == timedelta()
    assert time_manager.total_runtime == waiting_time
    assert time_manager.rolled_over_year_boundary is True


def test_exec_and_term_date():
    # test only execution and termination date given
    time_manager = TimeManager(None, exec_date, term_date)
    assert time_manager.submission_date is None
    fixed_exec_date = TimeManager.decrease_year(exec_date)
    assert time_manager.execution_date == fixed_exec_date
    assert time_manager.termination_date == term_date
    execution_runtime = term_date - fixed_exec_date
    assert time_manager.waiting_time == timedelta()
    assert time_manager.execution_time == execution_runtime
    assert time_manager.total_runtime == execution_runtime
    assert time_manager.rolled_over_year_boundary is True


def test_all_dates():
    # test all given
    time_manager = TimeManager(sub_date, exec_date, term_date)
    fixed_sub_date = TimeManager.decrease_year(sub_date)
    assert time_manager.submission_date == fixed_sub_date
    fixed_exec_date = TimeManager.decrease_year(exec_date)
    assert time_manager.execution_date == fixed_exec_date
    assert time_manager.termination_date == term_date
    waiting_time = fixed_exec_date - fixed_sub_date
    execution_time = term_date - fixed_exec_date
    total_runtime = term_date - fixed_sub_date
    assert time_manager.waiting_time == waiting_time
    assert time_manager.execution_time == execution_time
    assert time_manager.total_runtime == total_runtime
    assert time_manager.rolled_over_year_boundary is True
