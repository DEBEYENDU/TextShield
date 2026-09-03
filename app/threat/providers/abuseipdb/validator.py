from __future__ import annotations

import ipaddress
from typing import Tuple


def is_valid_ipv4(ip: str) -> bool:
    try:
        addr = ipaddress.IPv4Address(ip.strip())
        return True
    except Exception:
        return False


def is_valid_ipv6(ip: str) -> bool:
    try:
        addr = ipaddress.IPv6Address(ip.strip())
        return True
    except Exception:
        return False


def is_valid_ip(ip: str) -> bool:
    if not ip or not isinstance(ip, str):
        return False
    ip = ip.strip()
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def validate_lookup_input(value: str, ioc_type: str = "ip") -> Tuple[bool, str]:
    if not value or not isinstance(value, str):
        return False, "Input must be a non-empty string"
    value = value.strip()
    if not value:
        return False, "Input must be a non-empty string"
    if ioc_type in ("ip", "ipv4", "ipv6"):
        if not is_valid_ip(value):
            return False, f"Invalid IP address: {value}"
        if ioc_type == "ipv4" and not is_valid_ipv4(value):
            return False, f"Not a valid IPv4: {value}"
        if ioc_type == "ipv6" and not is_valid_ipv6(value):
            return False, f"Not a valid IPv6: {value}"
    else:
        return False, f"AbuseIPDB only supports IP lookups, got: {ioc_type}"
    return True, ""


def sanitize_ip(ip: str) -> str:
    if not ip:
        return ""
    return ip.strip()


def detect_ip_version(ip: str) -> str:
    ip = ip.strip()
    if is_valid_ipv4(ip):
        return "ipv4"
    if is_valid_ipv6(ip):
        return "ipv6"
    return "unknown"
