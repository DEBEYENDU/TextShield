from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.threat.ioc.models import IOCType
from app.threat.execution.models import LookupRequest, LookupResult, ThreatEvidence
from app.threat.providers.google_safe_browsing.models import (
    GoogleSafeBrowsingRequest, GoogleSafeBrowsingResponse
)

GoogleSafeBrowsingProvider.name = "google_safe_browsing"
GoogleSafeBrowsingProvider.version = "1.0.0"


class GoogleSafeBrowsingProvider:
    """Google Safe Browsing provider following the IThreatProvider abstraction."""

    def __init__(self, api_key: str = "", enabled: bool = True, **kwargs: Any):
        self._api_key = api_key
        self._enabled = enabled
        self._initialized = False
        self.ttl = kwargs.get("ttl", 3600)
        self.timeout = kwargs.get("timeout", 5.0)
        self.configuration = kwargs

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "capabilities": self.capabilities(),
            "ttl": self.ttl,
            "timeout": self.timeout,
            "api_key_configured": bool(self._api_key),
        }

    def capabilities(self) -> List[str]:
        return ["url_reputation", "malware", "social_engineering", "unsafe_downloads", "phishing"]

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    async def lookup_url(self, request: LookupRequest) -> Optional[ThreatIndicator]:
        if not self._api_key:
            return None
        # In production: call Google Safe Browsing API v4
        # For now simulate
        return await self._simulate_url_check(request.ioc)

    async def lookup_domain(self, request: LookupRequest) -> Optional[ThreatIndicator]:
        if not self._api_key:
            return None
        return await self._simulate_domain_check(request.ioc)

    async def lookup_ip(self, request: LookupRequest) -> Optional[ThreatIndicator]:
        if not self._api_key:
            return None
        return await self._simulate_ip_check(request.ioc)

    async def lookup_hash(self, request: LookupRequest) -> Optional[ThreatIndicator]:
        # Not primary for GSB, return None
        return None

    async def _simulate_url_check(self, url: str) -> Optional[ThreatIndicator]:
        # Heuristic simulation
        malicious_keywords = ["phishing", "malware", "scam", "bit.ly", "tinyurl.com"]
        url_lower = url.lower()
        is_mal = any(k in url_lower for k in malicious_keywords)
        if is_mal:
            conf = 0.75 if any(x in url_lower for x in ["bit.ly", "tinyurl.com"]) else 0.60
            sev = "high" if any(x in url_lower for x in ["bit.ly", "tinyurl.com"]) else "medium"
            return ThreatIndicator(
                indicator=url,
                indicator_type=IOCType.URL,
                provider=self.name,
                detection_status="malicious",
                confidence=conf,
                severity=sev,
                timestamp=datetime.now(timezone.utc),
                ttl=self.ttl,
                source="google_safe_browsing",
                explanation="Google Safe Browsing heuristic detection",
            )
        return None

    async def _simulate_domain_check(self, domain: str) -> Optional[ThreatIndicator]:
        domain_lower = domain.lower()
        if "phish" in domain_lower or "malware" in domain_lower:
            return ThreatIndicator(
                indicator=domain,
                indicator_type=IOCType.DOMAIN,
                provider=self.name,
                detection_status="malicious",
                confidence=0.70,
                severity="high",
                timestamp=datetime.now(timezone.utc),
                ttl=self.ttl,
                source="google_safe_browsing",
                explanation="Domain flagged by heuristics",
            )
        return None

    async def _simulate_ip_check(self, ip: str) -> Optional[ThreatIndicator]:
        parts = ip.split(".")
        if len(parts) == 4 and (all(p == "0" for p in parts) or all(p == "255" for p in parts)):
            return ThreatIndicator(
                indicator=ip,
                indicator_type=IOCType.IP,
                provider=self.name,
                detection_status="malicious",
                confidence=0.50,
                severity="medium",
                timestamp=datetime.now(timezone.utc),
                ttl=self.ttl,
                source="google_safe_browsing",
                explanation="Suspicious IP pattern",
            )
        return None

    @staticmethod
    def now_utc():
        return datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "api_key_configured": bool(self._api_key),
            "capabilities": self.capabilities(),
            "ttl": self.ttl,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoogleSafeBrowsingProvider":
        return cls(
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ("name", "version", "api_key", "enabled")},
        )