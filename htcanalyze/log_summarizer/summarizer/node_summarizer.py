"""Module to summarize node jobs."""
from typing import List

from htcanalyze.log_analyzer.condor_log.time_manager import JobTimes
from .summarizer import Summarizer
from ..summarized_condor_logs.summarized_node_jobs import (
    SingleNodeJob,
    SummarizedNodeJobs
)


class NodeJobCollection:
    """
    Create a Node-job collection of jobs executed on the same node.

    :param address: Address of the Node
    """

    def __init__(self, address: str):
        self.address = address
        self.nodes: List[SingleNodeJob] = []

    def add_node(self, node: SingleNodeJob):
        """Add a node."""
        assert node.address == self.address
        self.nodes.append(node)

    @property
    def n_jobs(self):
        """Returns number of jobs."""
        return len(self.nodes)

    @property
    def avg_job_times(self) -> JobTimes:
        """Returns average of job times of one node."""
        return sum(node.job_times for node in self.nodes) / self.n_jobs


class NodeManager:
    """
    Manage nodes by adding nodes to NodeJobCollections
    matching on the node addresses.
    """

    def __init__(self):
        self.nodes_dict = {}

    def add_node(self, node: SingleNodeJob):
        """Add node to nodes_dict."""
        try:
            self.nodes_dict[node.address].add_node(node)
        except KeyError:
            self.nodes_dict[node.address] = NodeJobCollection(node.address)
            self.nodes_dict[node.address].add_node(node)

    @property
    def node_collections(self) -> List[NodeJobCollection]:
        """Returns a list of NodJobCollection."""
        return list(self.nodes_dict.values())


class NodeSummarizer(Summarizer):

    """
    Summarize node jobs using a NodeManager.

    :param nodes: List of SingleNodeJob
    """
    def __init__(self, nodes: List[SingleNodeJob]):
        self.nodes = nodes
        self.node_manager = NodeManager()
        for node in self.nodes:
            self.node_manager.add_node(node)

    def summarize(self) -> List[SummarizedNodeJobs]:
        """Returns list of summarized node jobs."""
        return [
            SummarizedNodeJobs(
                node_collection.address,
                node_collection.avg_job_times,
                node_collection.n_jobs
            ) for node_collection in self.node_manager.node_collections
        ]
