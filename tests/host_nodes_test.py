
from htcanalyze.host_nodes import node_cache


def test_node_cache():
    node_cache.gethostbyaddrcached("172.217.0.0")
    assert node_cache.rdns_cache["172.217.0.0"] == "ord38s04-in-f0.1e100.net"
    node_cache.gethostbyaddrcached("172.217.0.0")  # lookup again
    node_cache.gethostbyaddrcached("NoIP")
    assert node_cache.rdns_cache["NoIP"] == "NoIP"