"""IOC normalization: canonical forms without destroying originals.

URL casing (host lowercased, path preserved), trailing punctuation,
IDNA/punycode, default ports, percent-encoding, domain case, hash case,
IPv4 octet formatting. Originals always preserved on the IOC.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse, urlunparse

from app.threat_intel.models import IOC

_DEFAULT_PORTS = {"http": 80, "https": 443, "ftp": 21}


def normalize_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return text
    if not re.match(r"(?i)^[a-z][a-z0-9+.-]*://", text):
        text = "http://" + text
    try:
        parts = urlparse(text)
    except Exception:
        return value.strip()
    host = (parts.hostname or "").lower()
    try:
        host = host.encode("idna").decode("ascii")
    except Exception:
        pass
    port = parts.port
    if port and _DEFAULT_PORTS.get(parts.scheme.lower()) == port:
        port = None
    netloc = host + (f":{port}" if port else "")
    if parts.username:
        netloc = parts.username + ("@" + netloc)
    path = unquote(parts.path or "")
    rebuilt = urlunparse((parts.scheme.lower(), netloc, path or "",
                          parts.params, parts.query, ""))
    return rebuilt.rstrip(".,;:!?") or value.strip()


def normalize_domain(value: str) -> str:
    host = (value or "").strip().lower().rstrip(".")
    if "://" in host:
        try:
            host = urlparse(host).hostname or host
        except Exception:
            pass
    host = host.split("/")[0].split(":")[0].split("@")[-1]
    try:
        return host.encode("idna").decode("ascii")
    except Exception:
        return host


def normalize_ip(value: str) -> str:
    parts = (value or "").strip().split(".")
    if len(parts) == 4:
        try:
            return ".".join(str(int(p)) for p in parts)
        except ValueError:
            pass
    return (value or "").strip().lower()


def normalize_hash(value: str) -> str:
    return (value or "").strip().lower()


def normalize_email(value: str) -> str:
    text = (value or "").strip()
    if "@" not in text:
        return text.lower()
    local, _, domain = text.partition("@")
    return f"{local}@{normalize_domain(domain)}"


def normalize_ioc(ioc: IOC) -> IOC:
    """Return a NEW IOC with normalized_value set; original preserved."""
    normalizers = {"url": normalize_url, "domain": normalize_domain,
                   "ipv4": normalize_ip, "ipv6": lambda v: v.strip().lower(),
                   "email": normalize_email, "md5": normalize_hash,
                   "sha1": normalize_hash, "sha256": normalize_hash}
    func = normalizers.get(ioc.ioc_type, lambda v: v.strip())
    try:
        normalized = func(ioc.original_value)
    except Exception:
        normalized = ioc.original_value.strip()
    return IOC(original_value=ioc.original_value,
               normalized_value=normalized or ioc.original_value.strip(),
               ioc_type=ioc.ioc_type, source_location=ioc.source_location,
               metadata=dict(ioc.metadata))


def normalize_all(iocs: list[IOC]) -> list[IOC]:
    return [normalize_ioc(ioc) for ioc in iocs]
