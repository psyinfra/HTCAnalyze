
from .summarizer import Summarizer, CondorLogSummarizer, StateSummarizer


class TimeSummarizer(Summarizer):

    def __init__(self, time_managers, ignore_empty=False):
        self.time_managers = time_managers
        self.ignore_empty = ignore_empty

    def summarize(self):
        pass


class HTCSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs):
        super(HTCSummarizer, self).__init__(condor_logs)

    def initialize_state_dict(self):
        state_dict = {}
        for condor_log in self.condor_logs:
            state_name = condor_log.job_details.state_manager.state
            if state_name in state_dict:
                state_dict[state_name].append(condor_log)
            else:
                state_dict[state_name] = [condor_log]

        return state_dict

    def summarize(self):
        state_dict = self.initialize_state_dict()
        state_summarizers = [
            StateSummarizer(condor_logs, state)
            for state, condor_logs in state_dict.items()
        ]
        for summarizer in state_summarizers:
            summarizer.summarize()  # Todo

        return self.condor_logs
