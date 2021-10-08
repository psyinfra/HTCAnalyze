
import json
from typing import List
from .summarizer import Summarizer
from htcanalyze.log_analyzer.condor_log import JobDetails, JobTimes


class SingleNode:
    """Single Node saving runtime on a node specified by ip or description."""

    def __init__(
            self,
            ip_or_address: str = None,
            job_times: JobTimes = None
    ):
        self.ip_or_address = ip_or_address
        self.job_times = job_times

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )


class NodeCollection:

    def __init__(self):
        self.node_collection = {}

    def add_node(self, node: SingleNode):
        try:
            self.node_collection[node.ip_or_address].append(node.job_times)
        except KeyError:
            self.node_collection[node.ip_or_address] = [node.job_times]

    def get_node(self, key):
        return self.node_collection[key]


class NodeSummarizer(Summarizer):

    def __init__(self, job_details: List[JobDetails]):
        self.nodes = [
            SingleNode(
                jd.host_address,
                jd.time_manager.job_times
            ) for jd in job_details
        ]
        self.node_collection = NodeCollection()
        for node in self.nodes:
            self.node_collection.add_node(node)

    def summarize(self) -> List[SingleNode]:
        return [
            SingleNode(
                ip_or_address,
                sum(job_times for job_times in all_job_times)
            )
            for ip_or_address, all_job_times in
            self.node_collection.node_collection.items()
        ]
