"""Mock provider: deterministic offline verdicts for tests and demos.

Flags well-known malicious patterns (shorteners with phishing paths,
RFC-2606-style test traps are benign) without any network access.
"""

from __future__ import annotations

import re

from app.threat_intel.models import ProviderResult
from app.threat_intel.provider import ThreatIntelProvider

_MALICIOUS_HINTS = re.compile(
    r"(phish|malware|ransom|trojan|keylogger|credential|stealer|"
    r"free-money|claim-prize|verify-account|suspended|sbi-kyc)",
    re.IGNORECASE)
_BENIGN_HOSTS = {"example.com", "example.org", "example.net",
                 "google.com", "microsoft.com", "rbi.org.in"}


class MockProvider(ThreatIntelProvider):
    """Zero-dependency reference provider (always configured)."""

    name = "mock"
    version = "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        return ["url", "domain", "ipv4", "ipv6", "md5", "sha1", "sha256"]

    def _verdict_for(self, value: str) -> tuple[str, float, str]:
        lowered = value.lower()
        host = lowered.split("/")[0]
        if host in _BENIGN_HOSTS or lowered in _BENIGN_HOSTS:
            return ("benign", 0.9, "well-known benign host")
        if _MALICIOUS_HINTS.search(lowered):
            return ("known_malicious", 0.85, "matches mock malicious pattern")
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host or lowered):
            return ("suspicious", 0.55, "raw IP host")
        if len(lowered) > 60 or host.count(".") >= 3:
            return ("suspicious", 0.5, "abnormal host structure")
        return ("unknown", 0.0, "no mock intelligence")

    def _result(self, value: str, ioc_type: str) -> ProviderResult:
        verdict, confidence, reason = self._verdict_for(value)
        return ProviderResult(ioc=value, ioc_type=ioc_type, provider=self.name,
                              verdict=verdict, confidence=confidence,
                              categories=["mock"],
                              sources=["mock-patterns-v1"],
                              raw_summary=reason)

    def lookup_url(self, url: str) -> ProviderResult:
        return self._result(url, "url")

    def lookup_domain(self, domain: str) -> ProviderResult:
        return self._result(domain, "domain")

    def lookup_ip(self, ip: str) -> ProviderResult:
        return self._result(ip, "ipv4")

    def lookup_hash(self, hash_value: str) -> ProviderResult:
        return self._result(hash_value, "sha256")
