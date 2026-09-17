from __future__ import annotations

import re
from typing import Tuple
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
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
    if not domain or not isinstance(domain, str):
        return False
    domain = domain.strip().lower()
    if len(domain) < 3 or len(domain) > 253:
        return False
    pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    return bool(re.match(pattern, domain))


def validate_lookup_input(value: str, ioc_type: str = "url") -> Tuple[bool, str]:
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
        if ioc_type not in ("url", "domain"):
            return False, f"PhishTank does not support IOC type: {ioc_type}"
    return True, ""


def sanitize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.endswith(":80") and parsed.scheme == "http":
            netloc = netloc[:-3]
        if netloc.endswith(":443") and parsed.scheme == "https":
            netloc = netloc[:-4]
        return parsed._replace(netloc=netloc).geturl()
    except Exception:
        return url
