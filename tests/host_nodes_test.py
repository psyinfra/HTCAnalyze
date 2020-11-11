
from htcanalyze.host_nodes import node_cache


def test_node_cache():
    node_cache.get_host_by_addr_cached("172.217.0.0")
    # might change in future, if the test fails here,
    # please use a new address to proof the functionality
    assert node_cache.rdns_cache["172.217.0.0"] == "ord38s04-in-f0.1e100.net"
    node_cache.get_host_by_addr_cached("172.217.0.0")  # lookup again (cov)
    node_cache.get_host_by_addr_cached("NoIP")
    assert node_cache.rdns_cache["NoIP"] == "NoIP"
