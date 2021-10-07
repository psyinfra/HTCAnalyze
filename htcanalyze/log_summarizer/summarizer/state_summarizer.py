from abc import abstractmethod
from typing import List

from htcanalyze.log_analyzer.event_handler import JobState
from htcanalyze.log_analyzer.condor_log import CondorLog
from .condor_log_summarizer import CondorLogSummarizer


class NormalStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(NormalStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.NORMAL_TERMINATION
            # Todo


class AbnormalStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbnormalStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.ABNORMAL_TERMINATION
            # Todo


class WaitingStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(WaitingStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.WAITING
            # Todo


class RunningStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(RunningStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.RUNNING
            # Todo


class AbortedStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(AbortedStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.ABORTED
            # Todo


class ErrorWhileReadingStateSummarizer(CondorLogSummarizer):
    def __init__(self, condor_logs: List[CondorLog]):
        super(ErrorWhileReadingStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        for condor_log in self.condor_logs:
            state_manager = condor_log.job_details.state_manager
            assert state_manager.state == JobState.ERROR_WHILE_READING
            # Todo


class StateSummarizer(CondorLogSummarizer):

    def __new__(cls, condor_logs, state: JobState = None):
        if state == JobState.NORMAL_TERMINATION:
            new = NormalStateSummarizer(condor_logs)
        elif state == JobState.ABNORMAL_TERMINATION:
            new = AbnormalStateSummarizer(condor_logs)
        elif state == JobState.RUNNING:
            new = RunningStateSummarizer(condor_logs)
        elif state == JobState.WAITING:
            new = WaitingStateSummarizer(condor_logs)
        elif state == JobState.ABORTED:
            new = AbortedStateSummarizer(condor_logs)
        elif state == JobState.ERROR_WHILE_READING:
            new = ErrorWhileReadingStateSummarizer(condor_logs)
        else:
            raise ValueError(f"Unknown state: {state}")
            # new = object.__new__(cls)
            # new.condor_logs = condor_logs

        return new

    @abstractmethod
    def summarize(self):
        pass
