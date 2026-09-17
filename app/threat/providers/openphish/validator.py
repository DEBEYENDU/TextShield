from __future__ import annotations

import re
from typing import Any, Dict, Tuple
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Validate that a string is a well-formed URL."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if len(url) < 8 or len(url) > 2048:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        if "." not in parsed.netloc:
            return False
        return True
    except Exception:
        return False


def is_valid_domain(domain: str) -> bool:
    """Validate domain format."""
    if not domain or not isinstance(domain, str):
        return False
    domain = domain.strip().lower()
    if len(domain) < 3 or len(domain) > 253:
        return False
    pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    return bool(re.match(pattern, domain))


def validate_lookup_input(value: str, ioc_type: str = "url") -> Tuple[bool, str]:
    """Validate lookup input and return (is_valid, error_message)."""
    if not value or not isinstance(value, str):
        return False, "Input must be a non-empty string"
    value = value.strip()
    if not value:
        return False, "Input must be a non-empty string"

    if ioc_type == "url":
        if not is_valid_url(value):
            return False, f"Invalid URL format: {value}"
    elif ioc_type == "domain":
        if not is_valid_domain(value):
            return False, f"Invalid domain format: {value}"
    else:
        # OpenPhish only supports URL
        if ioc_type not in ("url", "domain"):
            return False, f"OpenPhish does not support IOC type: {ioc_type}"

    return True, ""


def sanitize_url(url: str) -> str:
    """Sanitize and normalize URL for lookup."""
    if not url:
        return ""
    url = url.strip()
    # Ensure scheme present
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    # Lowercase host, preserve path case
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        # Remove default ports
        if netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]
        if netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]
        sanitized = parsed._replace(netloc=netloc).geturl()
        return sanitized
    except Exception:
        return url
