"""Manage times of HTCondor job logs."""
import json

from datetime import datetime as date_time, timedelta

from ..event_handler.set_events import SETEvents


class TimeDeltaWrapper(timedelta):

    def __new__(cls, time_delta: timedelta):
        if time_delta:
            return timedelta.__new__(
                cls,
                days=time_delta.days,
                seconds=time_delta.seconds
            )
        return timedelta.__new__(cls)

    @property
    def __dict__(self):
        return str(self)

    def __repr__(self):
        if self == timedelta():
            return str(None)
        return str(self)


class JobTimes:

    def __init__(
            self,
            waiting_time=None,
            execution_time=None,
            total_runtime=None
    ):
        self.waiting_time = TimeDeltaWrapper(waiting_time)
        self.execution_time = TimeDeltaWrapper(execution_time)
        self.total_runtime = TimeDeltaWrapper(total_runtime)

    def is_empty(self):
        return (
                self.waiting_time == timedelta() and
                self.execution_time == timedelta() and
                self.total_runtime == timedelta()
        )

    def __add__(self, other):
        return JobTimes(
            self.waiting_time + other.waiting_time,
            self.execution_time + other.execution_time,
            self.total_runtime + other.total_runtime
        )

    def __radd__(self, other):
        return self if other == 0 else self + other

    def __truediv__(self, other):
        return JobTimes(
            self.waiting_time / other,
            self.execution_time / other,
            self.total_runtime / other
        )

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )


class TimeManager:
    """
    Manage time differences and representation.

    This class creates time differences between the
    submission, execution and termination date of one job log
    By that it calculates the runtime.

    Furthermore it can be returned as a dictionary resolving the year,
    only if the job was running of new year.

    """

    def __init__(
            self,
            submission_date: date_time,
            execution_date: date_time,
            termination_date: date_time
    ):
        self.submission_date = submission_date
        self.execution_date = execution_date
        self.termination_date = termination_date
        self.rolled_over_year_boundary = False
        self._fix_dates_if_rolled_over(
            self.submission_date,
            self.execution_date,
            self.termination_date
        )
        self.job_times = self._manage_times()

    @classmethod
    def from_set_events(
            cls,
            set_events: SETEvents
    ):
        """Overload constructor to init with SETEvents."""
        return cls(
            set_events.submission_date,
            set_events.execution_date,
            set_events.termination_date
        )

    def is_empty(self):
        return (
                self.submission_date is None and
                self.execution_date is None and
                self.termination_date is None
        )

    def calc_waiting_time(self):
        if self.submission_date:
            if self.execution_date:
                return self.execution_date - self.submission_date
            elif self.termination_date:
                return self.termination_date - self.submission_date
            else:
                today = date_time.now()
                today = today.replace(microsecond=0)  # remove microseconds
                return today - self.submission_date

        return timedelta()

    def calc_execution_time(self):
        if self.execution_date:
            if self.termination_date:
                return self.termination_date - self.execution_date
            else:
                today = date_time.now()
                today = today.replace(microsecond=0)  # remove microseconds
                return today - self.execution_date

        return timedelta()

    def _manage_times(self) -> JobTimes:
        """
        Calculate the waiting, execution and total runtime.

        Check also if the times are overlapping in years.

        """
        waiting_time = self.calc_waiting_time()
        execution_time = self.calc_execution_time()
        total_runtime = waiting_time + execution_time

        return JobTimes(
            waiting_time,
            execution_time,
            total_runtime
        )

    @staticmethod
    def decrease_year(date, val=1):
        try:
            return date.replace(
                year=date.year - val
            )
        except ValueError as err:
            if err.args[0] == 'day is out of range for month':
                # Likely due to leap year (29.02)
                # Todo: fix whenever possible with htcondor module
                return date

    def _fix_dates_if_rolled_over(
            self,
            sub_date,
            exec_date,
            term_date
    ):
        """
        Decrease the year value of dates if a job rolled-over year boundary.
        The year value is ambigious and not available in a log file.
        This should help to calculate time differences correctly.

        Jobs running more than 365 days will NOT be managed correctly.

        :param sub_date:
        :param exec_date:
        :param term_date:
        :return:
        """
        # calculate the time difference to last year,
        # if the date is higher that today of running jobs
        # this means the execution started before the year overlap
        rolled_over_year_boundary = False
        if term_date is None:
            today = date_time.now()
            today = today.replace(microsecond=0)  # remove microseconds
            if sub_date and sub_date > today:
                rolled_over_year_boundary = True
                sub_date = self.decrease_year(sub_date)
            if exec_date and exec_date > today:
                rolled_over_year_boundary = True
                exec_date = self.decrease_year(exec_date)
        else:
            if exec_date and exec_date > term_date:
                rolled_over_year_boundary = True
                exec_date = self.decrease_year(exec_date)
            if sub_date and sub_date > term_date:
                rolled_over_year_boundary = True
                sub_date = self.decrease_year(sub_date)

        if sub_date and exec_date:
            if sub_date > exec_date:
                rolled_over_year_boundary = True
                sub_date = self.decrease_year(sub_date)

        self.submission_date = sub_date
        self.execution_date = exec_date
        self.termination_date = term_date
        self.rolled_over_year_boundary = rolled_over_year_boundary

    @property
    def waiting_time(self):
        return self.job_times.waiting_time

    @property
    def execution_time(self):
        return self.job_times.execution_time

    @property
    def total_runtime(self):
        return self.job_times.total_runtime

    @property
    def __dict__(self):
        return {
            "submission_date": str(self.submission_date),
            "execution_date": str(self.execution_date),
            "termination_date": str(self.termination_date),
            "waiting_time": str(self.waiting_time),
            "execution_time": str(self.execution_time),
            "total_runtime": str(self.total_runtime),
            "rolled_over_year_boundary": str(self.rolled_over_year_boundary)
        }

    def __repr__(self):
        return json.dumps(self.__dict__)
