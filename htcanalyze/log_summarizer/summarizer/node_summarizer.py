import json
from typing import List
from .summarizer import Summarizer
from htcanalyze.log_analyzer.condor_log import JobDetails, JobTimes


class SingleNodeJob:
    """Single Node saving runtime on a node specified by ip or description."""

    def __init__(
            self,
            address: str = None,
            job_times: JobTimes = None
    ):
        self.address = address
        self.job_times = job_times

    def __repr__(self):
        return json.dumps(
            self.__dict__,
            indent=2,
            default=lambda x: x.__dict__
        )


class SummarizedNodeJobs(SingleNodeJob):
    """
    Create a summarized job representation of jobs executed on a single node.

    :param address: Address of the node
    :param job_times: average job times
    :param n_jobs: Number of jobs executed on the node
    """
    def __init__(
            self,
            address: str = None,
            job_times: JobTimes = None,
            n_jobs: int = None
    ):
        super(SummarizedNodeJobs, self).__init__(address, job_times)
        self.n_jobs = n_jobs

    def __lt__(self, other):
        return self.n_jobs < other.n_jobs


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
            SingleNodeJob(
                jd.host_address,
                jd.time_manager.job_times
            ) for jd in job_details
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
