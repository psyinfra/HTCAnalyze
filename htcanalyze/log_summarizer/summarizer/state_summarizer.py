from abc import abstractmethod
from typing import List

from htcanalyze.log_analyzer.event_handler import JobState
from htcanalyze.log_analyzer.condor_log import CondorLog, JobTimes, LogResources
from .condor_log_summarizer import CondorLogSummarizer
from .time_summarizer import TimeSummarizer
from .log_resource_summarizer import LogResourceSummarizer
from .node_summarizer import NodeSummarizer, SingleNode


class SummarizedCondorLogs:

    def __init__(
            self,
            avg_times: JobTimes,
            avg_resources: LogResources,
            nodes: List[SingleNode]
    ):
        self.avg_times = avg_times
        self.avg_resources = avg_resources
        self.nodes = nodes


class NormalStateSummarizer(CondorLogSummarizer):

    def __init__(self, condor_logs: List[CondorLog]):
        super(NormalStateSummarizer, self).__init__(condor_logs)

    def summarize(self):
        resource_summarizer = LogResourceSummarizer(
            [cl.job_details.resources for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_resources = resource_summarizer.summarize()
        print(avg_resources)

        time_summarizer = TimeSummarizer(
            [cl.job_details.time_manager for cl in self.condor_logs],
            ignore_empty=False  # Todo
        )
        avg_times = time_summarizer.summarize()
        print(avg_times)

        node_summarizer = NodeSummarizer(
            [cl.job_details for cl in self.condor_logs]
        )
        nodes = node_summarizer.summarize()
        print(nodes)

        return SummarizedCondorLogs(
            avg_times,
            avg_resources,
            nodes
        )


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
