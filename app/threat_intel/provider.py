"""Provider abstraction: common ThreatIntelProvider interface.

Every provider supports lookup_url/domain/ip/hash/email where capable.
Verdicts: known_malicious | suspicious | unknown | benign |
unavailable | unsupported. UNKNOWN is never treated as SAFE downstream.
Synchronous by design (offline-first); adapters may wrap async clients.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.threat_intel.models import IOC, ProviderResult


class ThreatIntelProvider(ABC):
    """Interface every threat-intel provider must implement."""

    name: str = "base"
    version: str = "1.0.0"

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """IOC types this provider can look up."""

    def is_configured(self) -> bool:
        """False when credentials/settings are absent (offline-safe)."""
        return True

    def health(self) -> dict:
        return {"name": self.name, "version": self.version,
                "configured": self.is_configured(),
                "capabilities": self.capabilities}

    # ------------------------------------------------------- lookups
    def lookup(self, ioc: IOC) -> ProviderResult:
        handler = {"url": self.lookup_url, "domain": self.lookup_domain,
                   "ipv4": self.lookup_ip, "ipv6": self.lookup_ip,
                   "md5": self.lookup_hash, "sha1": self.lookup_hash,
                   "sha256": self.lookup_hash,
                   "email": self.lookup_email}.get(ioc.ioc_type)
        if handler is None:
            return ProviderResult.unsupported(ioc.normalized_value,
                                              ioc.ioc_type, self.name)
        try:
            return handler(ioc.normalized_value)
        except Exception as exc:
            return ProviderResult(ioc=ioc.normalized_value,
                                  ioc_type=ioc.ioc_type, provider=self.name,
                                  verdict="unavailable", confidence=0.0,
                                  provider_status="error",
                                  raw_summary=f"{type(exc).__name__}")

    def lookup_url(self, url: str) -> ProviderResult:
        return ProviderResult.unsupported(url, "url", self.name)

    def lookup_domain(self, domain: str) -> ProviderResult:
        return ProviderResult.unsupported(domain, "domain", self.name)

    def lookup_ip(self, ip: str) -> ProviderResult:
        return ProviderResult.unsupported(ip, "ipv4", self.name)

    def lookup_hash(self, hash_value: str) -> ProviderResult:
        return ProviderResult.unsupported(hash_value, "sha256", self.name)

    def lookup_email(self, email: str) -> ProviderResult:
        return ProviderResult.unsupported(email, "email", self.name)
