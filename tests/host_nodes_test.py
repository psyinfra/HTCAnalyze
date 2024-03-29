
from htcanalyze.log_analyzer.event_handler.node_cache import NodeCache


def test_node_cache(monkeypatch):
    node_cache = NodeCache()
    node_cache.get_host_by_addr_cached("172.217.0.0")
    monkeypatch.setattr(
        node_cache, "rdns_cache", {"172.217.0.0": "chs08s03-in-f0.1e100.net"}
    )
    assert node_cache.rdns_cache["172.217.0.0"] == "chs08s03-in-f0.1e100.net"
    node_cache.get_host_by_addr_cached("172.217.0.0")  # lookup again (cov)
    node_cache.get_host_by_addr_cached("NoIP")
    assert node_cache.rdns_cache["NoIP"] == "NoIP"
