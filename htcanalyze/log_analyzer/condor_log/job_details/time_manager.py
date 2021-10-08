"""Manage times of HTCondor job logs."""

import json
from datetime import datetime as date_time, timedelta


class TimeDeltaWrapper(timedelta):

    def __new__(cls, time_delta: timedelta):
        if time_delta:
            return timedelta.__new__(
                cls,
                days=time_delta.days,
                seconds=time_delta.seconds,
                microseconds=time_delta.microseconds
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
            self.waiting_time is None and
            self.execution_time is None and
            self.total_runtime is None
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

    def __init__(self, set_events):

        self.submission_date = set_events.submission_date
        self.execution_date = set_events.execution_date
        self.termination_date = set_events.termination_date
        self.running_over_newyear = False
        self.job_times = self._manage_times()

    def _manage_times(self) -> JobTimes:
        """
        Calculate the waiting, execution and total runtime.

        Check also if the times are overlapping in years.

        """
        today = date_time.now()
        today = today.replace(microsecond=0)  # remove microseconds
        waiting_time = None
        execution_time = None
        total_runtime = None

        # calculate the time difference to last year,
        # if the date is higher that today of running jobs
        # this means the execution started before newyear
        if self.termination_date is None:
            if self.submission_date and self.submission_date > today:
                self.running_over_newyear = True
                self.submission_date = self.submission_date.replace(
                    year=self.submission_date.year - 1
                )
            if self.execution_date and self.execution_date > today:
                self.running_over_newyear = True
                self.execution_date = self.execution_date.replace(
                    year=self.execution_date.year - 1
                )

        if self.execution_date and self.submission_date:
            self.execution_date = self.execution_date
            # new year ?
            if self.submission_date > self.execution_date:
                self.running_over_newyear = True
                self.submission_date = self.submission_date.replace(
                    year=self.submission_date.year - 1)
            waiting_time = self.execution_date - self.submission_date

        if self.termination_date:
            if waiting_time:
                pass
            if self.execution_date:
                # new year ?
                if self.execution_date > self.termination_date:
                    self.running_over_newyear = True
                    self.execution_date = self.execution_date.replace(
                        year=self.execution_date.year - 1
                    )
                execution_time = self.termination_date - self.execution_date
            if self.submission_date:
                # new year ?
                if self.submission_date > self.termination_date:
                    self.running_over_newyear = True
                    self.submission_date = self.submission_date.replace(
                        year=self.submission_date.year - 1
                    )
                total_runtime = self.termination_date - self.submission_date

        # Process still running
        elif self.execution_date:
            execution_time = today - self.execution_date
        # Still waiting for execution
        elif self.submission_date:
            waiting_time = today - self.submission_date

        return JobTimes(
            waiting_time,
            execution_time,
            total_runtime
        )

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
            "running_over_newyear": str(self.running_over_newyear)
        }

    def __repr__(self):
        return json.dumps(self.__dict__)

