"""Utility functions."""

import socket

def resolve_host(hostname):
    """Return IP address string or None if resolution fails."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

def validate_port_range(start, end):
    """Return True if ports are in range and start <= end."""
    return 1 <= start <= 65535 and 1 <= end <= 65535 and start <= end

def safe_int(value, default=0):
    """Convert to int, return default on error."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
