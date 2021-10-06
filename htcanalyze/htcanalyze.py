"""module to summarize and analyze HTCondor log files."""

from typing import List
# import own module
from .log_analyzer import CondorLog, get_condor_log, SummarizedCondorLogs


class HTCAnalyze:
    """
    This class is able to analyze HTCondor Joblogs.

    The modes:
        analyze,
        summarize,
        analyzed-summary

    """

    # class MODE(Enum):
    #     ANALYZE = 0
    #     SUMMARIZE = 1

    def __init__(
            self,
            # mode: MODE,
            rdns_lookup=False
    ):
        # self.mode = mode
        self.rdns_cache = {}
        self.rdns_lookup = rdns_lookup

    def analyze(self, log_files: List[str]) -> List[CondorLog]:
        """
        Analyze the given log files one by one.

        :param log_files: list of valid HTCondor log files
        :return: list with information of each log file
        """

        if not log_files:
            raise_value_error("No files to analyze")

        for file in log_files:
            condor_log = get_condor_log(file, self.rdns_lookup)
            yield condor_log

    def summarize(self, condor_logs: List[CondorLog]) -> SummarizedCondorLogs:
        summarized_logs = SummarizedCondorLogs(condor_logs)
        return summarized_logs


def raise_value_error(message: str) -> ValueError:
    """
    Raise Value Error with message.

    :param message: str
    :return:
    """
    raise ValueError(message)


def raise_type_error(message: str) -> TypeError:
    """
    Raise Type Error with message.

    :param message:
    :return:
    """
    raise TypeError(message)
