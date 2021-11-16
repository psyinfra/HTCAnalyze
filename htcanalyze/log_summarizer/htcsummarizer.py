"""Module to summarize all condor log files regarding the state."""
from typing import List

from htcanalyze.log_analyzer.event_handler.states import (
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
from .summarized_condor_logs.summarized_condor_logs import (
    SummarizedCondorLogs
)


class HTCSummarizer(CondorLogSummarizer):
    """Summarizer for ALL given condor log files."""

    def __init__(self, condor_logs):
        super().__init__(condor_logs)

    def _initialize_state_dict(self):
        """Initialize state dictionary."""
        state_dict = {}
        for condor_log in self.condor_logs:
            state = condor_log.job_details.state
            if state in state_dict:
                state_dict[state].append(condor_log)
            else:
                state_dict[state] = [condor_log]

        return state_dict

    @staticmethod
    def _get_summarizer_by_state(
            condor_logs,
            state
    ) -> CondorLogSummarizer:
        if isinstance(state, NormalTerminationState):
            return NormalTerminationStateSummarizer(condor_logs)
        if isinstance(state, AbnormalTerminationState):
            return AbnormalTerminationStateSummarizer(condor_logs)
        if isinstance(state, WaitingState):
            return WaitingStateSummarizer(condor_logs)
        if isinstance(state, RunningState):
            return RunningStateSummarizer(condor_logs)
        if isinstance(state, AbortedState):
            return AbortedStateSummarizer(condor_logs)
        if isinstance(state, ErrorWhileReadingState):
            return ErrorWhileReadingStateSummarizer(condor_logs)
        # else:
        raise ValueError(f"Unknown state: {state}")

    def summarize(self) -> List[SummarizedCondorLogs]:
        """Summarize logs per state."""
        state_dict = self._initialize_state_dict()
        state_summarizers = [
            self._get_summarizer_by_state(condor_logs, state)
            for state, condor_logs in state_dict.items()
        ]
        return [
            summarizer.summarize() for summarizer in state_summarizers
        ]
