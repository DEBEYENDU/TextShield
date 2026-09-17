"""Threat-intel data models: IOCs and normalized provider results."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field


@dataclass
class IOC:
    """A normalized Indicator of Compromise (original preserved)."""

    original_value: str
    normalized_value: str
    ioc_type: str  # url | domain | ipv4 | ipv6 | email | md5 | sha1 | sha256 | ...
    source_location: str = "message"  # message | sender | subject
    metadata: dict = field(default_factory=dict)

    def cache_key(self) -> str:
        return f"{self.ioc_type}:{self.normalized_value.lower()}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProviderResult:
    """Common normalized result every provider must return."""

    ioc: str
    ioc_type: str
    provider: str
    verdict: str  # known_malicious | suspicious | unknown | benign | unavailable | unsupported
    confidence: float = 0.0
    categories: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    checked_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    provider_status: str = "success"  # success | unavailable | rate_limited | error
    raw_summary: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["expired"] = time.time() > self.expires_at if self.expires_at else False
        return data

    @classmethod
    def unavailable(cls, ioc: str, ioc_type: str, provider: str,
                    reason: str = "unavailable") -> "ProviderResult":
        return cls(ioc=ioc, ioc_type=ioc_type, provider=provider,
                   verdict="unavailable", confidence=0.0,
                   provider_status=reason, raw_summary="provider unavailable")

    @classmethod
    def unsupported(cls, ioc: str, ioc_type: str, provider: str) -> "ProviderResult":
        return cls(ioc=ioc, ioc_type=ioc_type, provider=provider,
                   verdict="unsupported", confidence=0.0,
                   provider_status="success",
                   raw_summary=f"{provider} does not support {ioc_type} lookups")
