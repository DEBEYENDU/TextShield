"""Threat Intelligence & IOC Intelligence Platform (v4.0 / RFC-008).

Provider-independent framework for checking Indicators of Compromise
(URLs, domains, IPs, emails, hashes) against external and local
intelligence. Offline-first: fully usable with zero providers
configured. Never crawls URLs, never ships full messages externally.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-008"

VERDICTS = ("known_malicious", "suspicious", "unknown", "benign",
            "unavailable", "unsupported")

IOC_TYPES = ("url", "domain", "ipv4", "ipv6", "email", "md5", "sha1",
             "sha256", "phone", "crypto_wallet")
