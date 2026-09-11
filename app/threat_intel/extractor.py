"""Robust IOC extraction: URLs, domains, IPv4/IPv6, emails, hashes.

Guards: no bare numbers as IPs (octet validation), no plain words as
domains (TLD allowlist + dot requirement), bounded lengths, minimal
personal data (phones/crypto excluded here by design).
"""

from __future__ import annotations

import re

from app.threat_intel.models import IOC

_URL_RE = re.compile(
    r"(?:https?://|ftp://|www\.)[^\s<>\"]{4,2048}", re.IGNORECASE)
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,24}")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b")
_MD5_RE = re.compile(r"(?<![a-fA-F0-9])[a-fA-F0-9]{32}(?![a-fA-F0-9])")
_SHA1_RE = re.compile(r"(?<![a-fA-F0-9])[a-fA-F0-9]{40}(?![a-fA-F0-9])")
_SHA256_RE = re.compile(r"(?<![a-fA-F0-9])[a-fA-F0-9]{64}(?![a-fA-F0-9])")
_BARE_DOMAIN_RE = re.compile(
    r"(?<![A-Za-z0-9@/:])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)"
    r"(?:[A-Za-z]{2,24})(?![A-Za-z0-9.])")

_COMMON_TLDS = frozenset(
    "com net org io in co uk us gov edu info biz app dev ai me tech online "
    "site store top xyz tk ml ga cf gq dev moe".split())

_TRAIL_PUNCT = ".,;:!?'\")]}>"


def _strip_trailing(value: str) -> str:
    return value.rstrip(_TRAIL_PUNCT)


def _valid_ipv4(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 and (len(p) == 1 or not p.startswith("0"))
                   for p in parts)
    except ValueError:
        return False


def extract_iocs(text: str, source_location: str = "message",
                 max_per_type: int = 20) -> list[IOC]:
    """Extract IOCs with light normalization; full normalization is separate."""
    text = text or ""
    found: list[IOC] = []
    seen: set[tuple[str, str]] = set()

    def add(ioc_type: str, value: str):
        value = _strip_trailing(value.strip())
        if not value or len(value) > 2048:
            return
        key = (ioc_type, value.lower())
        if key in seen or len([f for f in found if f.ioc_type == ioc_type]) >= max_per_type:
            return
        seen.add(key)
        found.append(IOC(original_value=value, normalized_value=value,
                         ioc_type=ioc_type, source_location=source_location))

    for match in _URL_RE.finditer(text):
        add("url", match.group(0))
    for match in _EMAIL_RE.finditer(text):
        add("email", match.group(0))
    for match in _IPV4_RE.finditer(text):
        if _valid_ipv4(match.group(0)):
            add("ipv4", match.group(0))
    for match in _IPV6_RE.finditer(text):
        candidate = match.group(0).strip(":")
        if candidate.count(":") >= 2 and len(candidate) >= 4:
            add("ipv6", candidate)
    for pattern, ioc_type in ((_SHA256_RE, "sha256"), (_SHA1_RE, "sha1"),
                              (_MD5_RE, "md5")):
        for match in pattern.finditer(text):
            add(ioc_type, match.group(0))
    url_spans = [(m.start(), m.end()) for m in _URL_RE.finditer(text)]
    email_spans = [(m.start(), m.end()) for m in _EMAIL_RE.finditer(text)]

    def _inside(pos: int) -> bool:
        return any(s <= pos < e for s, e in url_spans + email_spans)

    for match in _BARE_DOMAIN_RE.finditer(text):
        if _inside(match.start()):
            continue
        tld = match.group(0).rsplit(".", 1)[-1].lower()
        if tld not in _COMMON_TLDS:
            continue
        add("domain", match.group(0))
    return found


class IOCExtractor:
    """Object wrapper (configurable caps) around :func:`extract_iocs`."""

    def __init__(self, max_per_type: int = 20):
        self.max_per_type = max_per_type

    def extract(self, text: str, source_location: str = "message") -> list[IOC]:
        return extract_iocs(text, source_location, self.max_per_type)
