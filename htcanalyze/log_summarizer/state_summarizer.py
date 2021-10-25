from abc import abstractmethod
from htcanalyze.log_analyzer.event_handler.states import JobState
from .summarizer.condor_log_summarizer import (
    CondorLogSummarizer,
    NormalTerminationStateSummarizer,
    AbnormalTerminationStateSummarizer,
    WaitingStateSummarizer,
    RunningStateSummarizer,
    AbortedStateSummarizer,
    ErrorWhileReadingStateSummarizer
)


class StateSummarizer(CondorLogSummarizer):

    def __new__(cls, condor_logs, state: JobState = None):
        if state == JobState.NORMAL_TERMINATION:
            new = NormalTerminationStateSummarizer(condor_logs)
        elif state == JobState.ABNORMAL_TERMINATION:
            new = AbnormalTerminationStateSummarizer(condor_logs)
        elif state == JobState.WAITING:
            new = WaitingStateSummarizer(condor_logs)
        elif state == JobState.RUNNING:
            new = RunningStateSummarizer(condor_logs)
        elif state == JobState.ABORTED:
            new = AbortedStateSummarizer(condor_logs)
        elif state == JobState.ERROR_WHILE_READING:
            new = ErrorWhileReadingStateSummarizer(condor_logs)
        else:
            raise ValueError(f"Unknown state: {state}")
            # new = object.__new__(cls)
            # new.condor_logs = condor_logs

        new.state = state

        return new

    @abstractmethod
    def summarize(self):
        pass
