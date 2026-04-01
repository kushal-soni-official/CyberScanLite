"""Platform‑independent ping implementation."""

import subprocess
import platform
import re

def ping_host(host):
    """Return (reachable, ttl) where reachable is bool and ttl is int or None."""
    # Determine ping command based on OS
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", "2000", host]
        ttl_pattern = r"TTL=(\d+)"
    else:
        # Linux/macOS
        cmd = ["ping", "-c", "1", "-W", "2", host]
        ttl_pattern = r"ttl=(\d+)"
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError:
        return False, None
    # Search for TTL
    match = re.search(ttl_pattern, output, re.IGNORECASE)
    if match:
        ttl = int(match.group(1))
        return True, ttl
    # If no TTL found but command succeeded, treat as reachable but TTL unknown
    if output:
        return True, None
    return False, None
