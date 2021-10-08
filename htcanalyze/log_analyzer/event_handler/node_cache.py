"""Class to store host nodes."""
import socket
import logging


class NodeCache:
    """Cache to save reverse DNS lookups."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NodeCache, cls).__new__(
                cls, *args, **kwargs
            )
            cls._instance.rdns_cache = {}
        return cls._instance

    def get_host_by_addr_cached(self, ip_address):
        """
        Get the hostname by address, with an in-memory cache.

        This prevents excessive queries to DNS servers.

        :param ip_address: ip_address represented by a string
        :return: resolved domain name, else give back the IP
        """
        try:
            # try our cache first
            return self.rdns_cache[ip_address]
        except KeyError:
            # do the lookup
            try:
                rdns = socket.gethostbyaddr(ip_address)
                logging.debug(f"rDNS lookup successful: "
                              f"{ip_address} resolved as {rdns[0]}")
                self.rdns_cache[ip_address] = rdns[0]
                return rdns[0]
            except socket.error:
                logging.debug(
                    f"Unable to perform rDNS lookup for {ip_address}"
                )
                # cache negative responses too
                self.rdns_cache[ip_address] = ip_address
                return ip_address
