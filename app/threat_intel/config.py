"""Threat-intel configuration: env-driven, secrets never logged."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass
class ThreatIntelConfig:
    """All knobs; API keys come from the environment only."""

    google_safe_browsing_key: str = field(
        default_factory=lambda: _get("TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY"))
    virustotal_key: str = field(
        default_factory=lambda: _get("TEXTSHIELD_VIRUSTOTAL_API_KEY"))
    enabled_providers: tuple = ("mock", "static", "google_safe_browsing",
                                "virustotal")
    cache_ttl_seconds: int = 3600
    cache_path: str = "data/threat_intel_cache.json"
    provider_timeout_seconds: float = 5.0
    max_iocs_per_message: int = 10
    allow_external_lookups: bool = True
    # per-provider rate limits: {provider: (per_minute, per_day)}
    rate_limits: dict = field(default_factory=lambda: {
        "google_safe_browsing": (60, 10000),
        "virustotal": (4, 500),
        "mock": (1000, 100000),
        "static": (10000, 1000000),
    })

    @property
    def gsb_configured(self) -> bool:
        return bool(self.google_safe_browsing_key)

    @property
    def virustotal_configured(self) -> bool:
        return bool(self.virustotal_key)

    def redacted(self) -> dict:
        """Safe to log/API-expose: key presence only, never values."""
        return {"enabled_providers": list(self.enabled_providers),
                "google_safe_browsing_configured": self.gsb_configured,
                "virustotal_configured": self.virustotal_configured,
                "cache_ttl_seconds": self.cache_ttl_seconds,
                "allow_external_lookups": self.allow_external_lookups}


config = ThreatIntelConfig()
