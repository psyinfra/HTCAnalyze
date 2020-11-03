"""Class to store host nodes."""
import socket
import logging
from datetime import timedelta


class NodeCache:
    """Cache to save reverse DNS lookups."""

    def __init__(self):
        self.rdns_cache = dict()

    def gethostbyaddrcached(self, ip):
        """
        Get the hostname by address, with an in-memory cache.

        This prevents excessive queries to DNS servers.

        :param ip: ip represented by a string
        :return: resolved domain name, else give back the IP
        """
        try:
            # try our cache first
            return self.rdns_cache[ip]
        except KeyError:
            # do the lookup
            try:
                rdns = socket.gethostbyaddr(ip)
                logging.debug(f"rDNS lookup successful: "
                              f"{ip} resolved as {rdns[0]}")
                self.rdns_cache[ip] = rdns[0]
                return rdns[0]
            except socket.error:
                logging.debug(f"Unable to perform rDNS lookup for {ip}")
                # cache negative responses too
                self.rdns_cache[ip] = ip
                return ip


# global instance to cache reverse dns lookup
node_cache = NodeCache()


class SingleNode:
    """Single Node saving runtime on a node specified by ip or description."""

    def __init__(self, ip_or_desc: str = None, total_runtime=None):
        self.ip_or_desc = ip_or_desc
        self.total_runtime = total_runtime


class HostNodes:
    """Collection of nodes."""

    def __init__(self, rdns_lookup=False):
        self.nodes = dict()
        self.rdns_lookup = rdns_lookup

    def add_node(self, node: SingleNode):
        """
        Add a node to the nodes dictionary.

        Make a first entry with the ip or description
        or increase existing entries.

        :param node:
        :return:
        """
        key = node.ip_or_desc
        if self.rdns_lookup:
            key = node_cache.gethostbyaddrcached(key)

        try:
            self.nodes[key]['n_jobs'] += 1
            self.nodes[key]['tt_time'] += node.total_runtime
        except KeyError:
            self.nodes[key] = dict()
            self.nodes[key]['n_jobs'] = 1
            self.nodes[key]['tt_time'] = node.total_runtime

    def nodes_to_avg_dict(self) -> dict:
        """Create dict with average run times per node."""
        keys = self.nodes.keys()
        executed_jobs = list()
        avg_times_spend = list()
        for key in keys:
            n_jobs = self.nodes[key]['n_jobs']
            executed_jobs.append(n_jobs)
            avg_job_duration = self.nodes[key]['tt_time'] / n_jobs
            avg_times_spend.append(
                timedelta(avg_job_duration.days,
                          avg_job_duration.seconds)
            )

        return {
            "Host Nodes": keys,
            "Executed Jobs": executed_jobs,
            "Average job duration": avg_times_spend
        }
