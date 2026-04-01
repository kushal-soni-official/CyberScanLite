"""OS fingerprinting via TTL from ping."""

import yaml
import os
from scanner.ping import ping_host

class OSFingerprinter:
    def __init__(self, fingerprints_file=None):
        if fingerprints_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fingerprints_file = os.path.join(base_dir, "data", "os_fingerprints.yaml")
        with open(fingerprints_file, 'r') as f:
            self.fingerprints = yaml.safe_load(f)

    def guess_os(self, ip, open_port=None):
        """Return an OS guess based on TTL from ping."""
        reachable, ttl = ping_host(ip)
        if not reachable or ttl is None:
            return "Unknown (host unreachable or no TTL)"

        # Find closest match by TTL
        # For simplicity, find exact TTL match
        for fp in self.fingerprints:
            if fp["ttl"] == ttl:
                return fp["name"]
        # No exact match: approximate
        # If TTL is between 32 and 64, likely Linux/Unix; between 128 and 255, likely Windows
        if 32 <= ttl <= 64:
            return "Linux/Unix (TTL={})".format(ttl)
        elif 64 < ttl <= 128:
            return "Windows (TTL={})".format(ttl)
        else:
            return "Unknown (TTL={})".format(ttl)
