from abc import abstractmethod
from htcanalyze.log_analyzer.event_handler.states import (
    JobState,
    NormalTerminationState,
    AbnormalTerminationState,
    WaitingState,
    RunningState,
    AbortedState,
    ErrorWhileReadingState
)
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
        if isinstance(state, NormalTerminationState):
            new = NormalTerminationStateSummarizer(condor_logs)
        elif isinstance(state, AbnormalTerminationState):
            new = AbnormalTerminationStateSummarizer(condor_logs)
        elif isinstance(state, WaitingState):
            new = WaitingStateSummarizer(condor_logs)
        elif isinstance(state, RunningState):
            new = RunningStateSummarizer(condor_logs)
        elif isinstance(state, AbortedState):
            new = AbortedStateSummarizer(condor_logs)
        elif isinstance(state, ErrorWhileReadingState):
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
