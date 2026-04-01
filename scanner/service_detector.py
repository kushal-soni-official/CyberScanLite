"""Service detection via banner grabbing."""

import socket
import yaml
import os
import re

class ServiceDetector:
    def __init__(self, signatures_file=None):
        if signatures_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            signatures_file = os.path.join(base_dir, "data", "service_signatures.yaml")
        with open(signatures_file, 'r') as f:
            self.signatures = yaml.safe_load(f)
        # Flatten signatures into a list for easy lookup by port
        self.port_map = {}  # port -> list of (service_name, pattern, version_group, fallback)
        for service, entries in self.signatures.items():
            for entry in entries:
                port = entry["port"]
                pattern = entry.get("pattern")
                version_group = entry.get("version_group", 0)
                fallback = entry.get("fallback", service)
                if port not in self.port_map:
                    self.port_map[port] = []
                self.port_map[port].append((service, pattern, version_group, fallback))

    def detect(self, ip, port):
        """Return (service_name, version) for the given IP and port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))
            # Send a generic probe (e.g., empty line, or some common request)
            # For simplicity, just read banner
            # Some services require a send first; we'll try both: send a newline then read
            sock.send(b"\r\n")
            banner = sock.recv(1024).decode(errors='ignore')
            sock.close()
        except Exception:
            # If connection fails, no banner
            banner = ""

        # Match against signatures for this port
        if port in self.port_map:
            for (service_name, pattern, version_group, fallback) in self.port_map[port]:
                if pattern:
                    match = re.search(pattern, banner, re.IGNORECASE)
                    if match:
                        version = match.group(version_group) if version_group else ""
                        return service_name, version
                else:
                    # No pattern; just fallback
                    return fallback, ""
        # No signature matched; return generic
        return "unknown", ""
