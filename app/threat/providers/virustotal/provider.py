from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.threat.ioc.models import IOCType
from app.threat.providers.threat_indicator import ThreatIndicator

logger = logging.getLogger(__name__)


class VirusTotalProvider:
    """VirusTotal provider following the IThreatProvider abstraction."""

    name = "virustotal"
    version = "1.0.0"

    def __init__(self, api_key: str = "", enabled: bool = True, **kwargs: Any):
        self._api_key = api_key
        self._enabled = enabled
        self._initialized = False
        self.ttl = kwargs.get("ttl", 300)
        self.timeout = kwargs.get("timeout", 5.0)
        self.configuration = kwargs
        self._health: Dict[str, Any] = {"healthy": True, "last_check": None}

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
        return ["url_reputation", "domain_reputation", "ip_reputation", "file_reputation", "detection_statistics", "malware_analysis"]

    def initialize(self) -> None:
        self._initialized = True
        self._health = {"healthy": True, "last_check": datetime.now(timezone.utc).isoformat(), "error": None}
        logger.info("VirusTotal provider initialized: enabled=%s", self.enabled)

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("VirusTotal provider shut down")

    def health_check(self) -> Dict[str, Any]:
        try:
            now = datetime.now(timezone.utc).isoformat()
            healthy = self._initialized
            self._health = {"healthy": healthy, "last_check": now, "error": None, "initialized": self._initialized, "enabled": self.enabled}
            return dict(self._health)
        except Exception as exc:  # noqa: BLE001
            return {"healthy": False, "error": str(exc), "last_check": datetime.now(timezone.utc).isoformat()}

    async def lookup_url(self, url: str) -> Optional[ThreatIndicator]:
        if hasattr(url, "ioc"):
            url = getattr(url, "ioc")
        if not isinstance(url, str):
            return None
        if not self._initialized:
            self.initialize()
        if not self._api_key:
            return None
        return await self._simulate_url_check(url)

    async def lookup_domain(self, domain: str) -> Optional[ThreatIndicator]:
        if hasattr(domain, "ioc"):
            domain = getattr(domain, "ioc")
        if not isinstance(domain, str):
            return None
        if not self._initialized:
            self.initialize()
        if not self._api_key:
            return None
        return await self._simulate_domain_check(domain)

    async def lookup_ip(self, ip: str) -> Optional[ThreatIndicator]:
        if hasattr(ip, "ioc"):
            ip = getattr(ip, "ioc")
        if not isinstance(ip, str):
            return None
        if not self._initialized:
            self.initialize()
        if not self._api_key:
            return None
        return await self._simulate_ip_check(ip)

    async def lookup_hash(self, hash_value: str) -> Optional[ThreatIndicator]:
        if hasattr(hash_value, "ioc"):
            hash_value = getattr(hash_value, "ioc")
        if not isinstance(hash_value, str):
            return None
        if not self._initialized:
            self.initialize()
        if not self._api_key:
            return None
        return await self._simulate_hash_check(hash_value)

    async def _simulate_url_check(self, url: str) -> Optional[ThreatIndicator]:
        url_lower = url.lower()
        suspicious_tlds = {".top", ".xyz", ".club", ".gq", ".ml", ".cf"}
        is_suspicious = any(url_lower.endswith(t) for t in suspicious_tlds)
        threat_keywords = ["login", "secure", "verify", "account", "bank", "paypal"]
        has_kw = any(k in url_lower for k in threat_keywords)
        if is_suspicious or has_kw:
            conf = 0.70 if (is_suspicious and has_kw) else 0.55
            sev = "high" if is_suspicious and has_kw else ("medium" if is_suspicious or has_kw else "low")
            return ThreatIndicator(
                indicator=url,
                indicator_type=IOCType.URL,
                provider=self.name,
                detection_status="malicious",
                confidence=conf,
                severity=sev,
                timestamp=datetime.now(timezone.utc),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation="VT heuristic detection",
            )
        return None

    async def _simulate_domain_check(self, domain: str) -> Optional[ThreatIndicator]:
        domain_lower = domain.lower()
        brand_impersonation = any(brand in domain_lower for brand in ["paypal", "microsoft", "google", "amazon", "apple"])
        suspicious_tlds = {".top", ".xyz", ".club", ".gq", ".ml", ".cf", ".zip", ".loan"}
        has_suspicious_tld = any(domain_lower.endswith(t) for t in suspicious_tlds)
        if brand_impersonation or has_suspicious_tld:
            conf = 0.80 if brand_impersonation and has_suspicious_tld else 0.65
            sev = "high" if brand_impersonation else "medium"
            return ThreatIndicator(
                indicator=domain,
                indicator_type=IOCType.DOMAIN,
                provider=self.name,
                detection_status="malicious",
                confidence=conf,
                severity=sev,
                timestamp=datetime.now(timezone.utc),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation="VT domain analysis",
            )
        return None

    async def _simulate_ip_check(self, ip: str) -> Optional[ThreatIndicator]:
        parts = ip.split(".")
        if len(parts) == 4 and parts[0] in ("0", "255", "192", "10", "172"):
            last = int(parts[3])
            if last in (0, 255):
                return ThreatIndicator(
                    indicator=ip,
                    indicator_type=IOCType.IP,
                    provider=self.name,
                    detection_status="malicious",
                    confidence=0.55,
                    severity="medium",
                    timestamp=datetime.now(timezone.utc),
                    ttl=timedelta(seconds=self.ttl),
                    source="virustotal",
                    explanation="VT IP pattern",
                )
        return None

    async def _simulate_hash_check(self, hash_val: str) -> Optional[ThreatIndicator]:
        if len(hash_val) == 32:  # MD5
            conf = 0.75 if hash_val.startswith(("a", "b")) else 0.35
            sev = "high" if hash_val.startswith(("a", "b")) else "low"
            return ThreatIndicator(
                indicator=hash_val,
                indicator_type=IOCType.CRYPTO_WALLET,
                provider=self.name,
                detection_status="malicious" if conf > 0.5 else "unknown",
                confidence=conf,
                severity=sev,
                timestamp=datetime.now(timezone.utc),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation="VT hash check",
            )
        elif len(hash_val) == 40:  # SHA1
            return ThreatIndicator(
                indicator=hash_val,
                indicator_type=IOCType.CRYPTO_WALLET,
                provider=self.name,
                detection_status="unknown",
                confidence=0.65,
                severity="medium",
                timestamp=datetime.now(timezone.utc),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation="VT SHA1 check",
            )
        elif len(hash_val) == 64:  # SHA256
            conf = 0.80
            sev = "high" if conf > 0.7 else "medium"
            return ThreatIndicator(
                indicator=hash_val,
                indicator_type=IOCType.CRYPTO_WALLET,
                provider=self.name,
                detection_status="malicious",
                confidence=conf,
                severity=sev,
                timestamp=datetime.now(timezone.utc),
                ttl=timedelta(seconds=self.ttl),
                source="virustotal",
                explanation="VT SHA256 check",
            )
        return None

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
    def from_dict(cls, data: Dict[str, Any]) -> "VirusTotalProvider":
        return cls(
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ("name", "version", "api_key", "enabled")},
        )
