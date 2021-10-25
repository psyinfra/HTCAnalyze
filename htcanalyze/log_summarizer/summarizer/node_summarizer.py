from typing import List
from .summarizer import Summarizer
from ..summarized_condor_logs.summarized_node_jobs import (
    SingleNodeJob,
    SummarizedNodeJobs
)
from htcanalyze.log_analyzer.condor_log.job_details import JobDetails
from htcanalyze.log_analyzer.condor_log.time_manager import JobTimes


class NodeJobCollection:
    """
    Create a Node-job collection of jobs executed on the same node.

    :param address: Address of the Node
    """

    def __init__(self, address: str):

        self.address = address
        self.nodes: List[SingleNodeJob] = []

    def add_node(self, node: SingleNodeJob):
        assert node.address == self.address
        self.nodes.append(node)

    @property
    def n_jobs(self):
        return len(self.nodes)

    @property
    def avg_job_times(self) -> JobTimes:
        return sum(node.job_times for node in self.nodes) / self.n_jobs


class NodeManager:
    """
    Manage nodes by adding nodes to NodeJobCollections
    matching on the node addresses.
    """

    def __init__(self):
        self.nodes_dict = {}

    def add_node(self, node: SingleNodeJob):
        try:
            self.nodes_dict[node.address].add_node(node)
        except KeyError:
            self.nodes_dict[node.address] = NodeJobCollection(node.address)
            self.nodes_dict[node.address].add_node(node)

    @property
    def node_collections(self) -> List[NodeJobCollection]:
        return list(self.nodes_dict.values())


class NodeSummarizer(Summarizer):

    """
    Summarize node jobs using a NodeManager.

    :param job_details: List of JobDetails
    """
    def __init__(self, job_details: List[JobDetails]):

        self.nodes = [
            SingleNodeJob(jd.host_address, jd.job_times) for jd in job_details
        ]
        self.node_manager = NodeManager()
        for node in self.nodes:
            self.node_manager.add_node(node)

    def summarize(self) -> List[SummarizedNodeJobs]:
        return [
            SummarizedNodeJobs(
                node_collection.address,
                node_collection.avg_job_times,
                node_collection.n_jobs
            ) for node_collection in self.node_manager.node_collections
        ]
