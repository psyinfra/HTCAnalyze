"""Module to summarize all condor log files regarding the state."""
from typing import List

from .state_summarizer import StateSummarizer
from .summarized_condor_logs.summarized_condor_logs import SummarizedCondorLogs
from .summarizer.condor_log_summarizer import CondorLogSummarizer


class HTCSummarizer(CondorLogSummarizer):
    """Summarizer for ALL given condor log files."""

    def __init__(self, condor_logs):
        super().__init__(condor_logs)

    def initialize_state_dict(self):
        """Initialize state dictionary."""
        state_dict = {}
        for condor_log in self.condor_logs:
            state = condor_log.job_details.state
            if state in state_dict:
                state_dict[state].append(condor_log)
            else:
                state_dict[state] = [condor_log]

        return state_dict

    def summarize(self) -> List[SummarizedCondorLogs]:
        """Summarize logs per state."""
        state_dict = self.initialize_state_dict()
        state_summarizers = [
            StateSummarizer(condor_logs, state)
            for state, condor_logs in state_dict.items()
        ]
        return [
            summarizer.summarize() for summarizer in state_summarizers
        ]
