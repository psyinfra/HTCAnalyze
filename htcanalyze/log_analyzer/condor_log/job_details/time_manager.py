"""Manage times of HTCondor job logs."""
import json
from typing import List
from datetime import datetime as date_time, timedelta


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
        self.waiting_time = None
        self.execution_time = None
        self.total_runtime = None

        self.running_over_newyear = False

        self._manage_times()

    def _manage_times(self):
        """
        Calculate the waiting, execution and total runtime.

        Check also if the times are overlapping in years.

        """
        today = date_time.now()
        today = today.replace(microsecond=0)  # remove microseconds

        # calculate the time difference to last year,
        # if the date is higher that today of running jobs
        # this means the execution started before newyear
        if self.termination_date is None:
            if self.submission_date and self.submission_date > today:
                self.running_over_newyear = True
                self.submission_date = self.submission_date.replace(
                    year=self.submission_date.year - 1)
            if self.execution_date and self.execution_date > today:
                self.running_over_newyear = True
                self.execution_date = self.execution_date.replace(
                    year=self.execution_date.year - 1)

        if self.execution_date and self.submission_date:
            self.execution_date = self.execution_date
            # new year ?
            if self.submission_date > self.execution_date:
                self.running_over_newyear = True
                self.submission_date = self.submission_date.replace(
                    year=self.submission_date.year - 1)
            self.waiting_time = self.execution_date - self.submission_date

        if self.termination_date:
            if self.waiting_time:
                pass
            if self.execution_date:
                # new year ?
                if self.execution_date > self.termination_date:
                    self.running_over_newyear = True
                    self.execution_date = self.execution_date.replace(
                        year=self.execution_date.year - 1)
                self.execution_time = (self.termination_date -
                                       self.execution_date)
            if self.submission_date:
                # new year ?
                if self.submission_date > self.termination_date:
                    self.running_over_newyear = True
                    self.submission_date = self.submission_date.replace(
                        year=self.submission_date.year - 1)
                self.total_runtime = (self.termination_date -
                                      self.submission_date)
        # Process still running
        elif self.execution_date:
            self.execution_time = today - self.execution_date
        # Still waiting for execution
        elif self.submission_date:
            self.waiting_time = today - self.submission_date

    def create_time_dict(self) -> dict:
        """
        Return a fancy representation as a dict.

        The feature here, is that the year only gets represented
        if a job was running over new year.

        :return: dict
        """
        time_desc = []
        time_vals = []

        # now after collecting all available values try to produce a dict
        # if new year was hitted by one of them, show the year as well
        if self.running_over_newyear:
            if self.submission_date:
                time_desc.append("Submission date")
                time_vals.append(self.submission_date)
            if self.execution_date:
                time_desc.append("Execution date")
                time_vals.append(self.execution_date)
            if self.termination_date:
                time_desc.append("Termination date")
                time_vals.append(self.termination_date)
        else:
            if self.submission_date:
                time_desc.append("Submission date")
                time_vals.append(
                    self.submission_date.strftime("%m/%d %H:%M:%S"))
            if self.execution_date:
                time_desc.append("Execution date")
                time_vals.append(
                    self.execution_date.strftime("%m/%d %H:%M:%S"))
            if self.termination_date:
                time_desc.append("Termination date")
                time_vals.append(
                    self.termination_date.strftime("%m/%d %H:%M:%S"))

        if self.waiting_time:
            time_desc.append("Waiting time")
            time_vals.append(self.waiting_time)
        if self.execution_time:
            time_desc.append("Execution runtime")
            time_vals.append(self.execution_time)
        if self.total_runtime:
            time_desc.append("Total runtime")
            time_vals.append(self.total_runtime)

        if time_desc:
            return {
                "Dates and times": time_desc,
                "Values": time_vals
            }
        # else:
        return {}

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


def calc_avg_on_times(time_managers: List[TimeManager]) -> dict:
    """
    Calculate the average of a list with time managers.

    Only the the different time differences get added
    and divided by the number of time managers.

    :param time_managers: list of TimeManager's
    :return: dict with total and average time differences
    """
    # all values empty
    waiting_for = timedelta()
    executing_for = timedelta()
    total_running_time = timedelta()
    for manager in time_managers:
        waiting_for += manager.waiting_time
        executing_for += manager.execution_time
        total_running_time += manager.total_runtime

    n_times = len(time_managers)

    time_headers = []
    times = []
    av_times = []
    if waiting_for:
        time_headers.append("Waiting time")
        times.append(waiting_for)
        av_times.append(waiting_for/n_times)
    if executing_for:
        time_headers.append("Execution time")
        times.append(executing_for)
        av_times.append(executing_for/n_times)
    if total_running_time:
        time_headers.append("Total")
        times.append(total_running_time)
        av_times.append(total_running_time/n_times)

    format_av_times = [
        timedelta(days=time.days, seconds=time.seconds)
        for time in av_times]

    if times:
        return {
            "Times": time_headers,
            "Average": format_av_times,
            "Total": times
        }
    # else:
    return {}
