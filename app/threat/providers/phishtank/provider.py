from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.threat.ioc.models import IOCType
from app.threat.providers.threat_indicator import ThreatIndicator

from .client import PhishTankClient
from .config import PhishTankConfig
from .mapper import response_to_indicator
from .models import PhishTankRequest
from .validator import sanitize_url, validate_lookup_input

logger = logging.getLogger(__name__)


class PhishTankProvider:
    """PhishTank threat intelligence provider.

    Supports URL reputation + phishing metadata (verified, valid, detail URL).
    """

    name = "phishtank"
    version = "1.0.0"

    def __init__(self, api_key: Optional[str] = None, enabled: bool = True, **kwargs: Any):
        self._api_key = api_key
        self._enabled = enabled
        self._initialized = False
        self._config = PhishTankConfig(api_key=api_key or "", enabled=enabled, **kwargs)
        self.ttl: int = self._config.ttl
        self.timeout: float = self._config.timeout
        self.configuration: Dict[str, Any] = self._config.to_dict()
        self._client = PhishTankClient(
            api_url=self._config.api_url,
            api_key=self._config.api_key,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            backoff_factor=self._config.backoff_factor,
            rate_limit_per_minute=self._config.rate_limit_per_minute,
        )
        self._health: Dict[str, Any] = {"healthy": True, "last_check": None, "error": None}
        self._request_count = 0
        self._error_count = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._config.enabled = value

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
            "api_url": self._config.api_url,
            "rate_limit_per_minute": self._config.rate_limit_per_minute,
            "max_retries": self._config.max_retries,
        }

    def capabilities(self) -> List[str]:
        return ["url_reputation", "phishing_metadata", "verification_status", "phishing_details"]

    def initialize(self) -> None:
        self._initialized = True
        self._health = {"healthy": True, "last_check": datetime.now(timezone.utc).isoformat(), "error": None}
        logger.info("PhishTank provider initialized: enabled=%s", self.enabled)

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("PhishTank provider shut down")

    def health_check(self) -> Dict[str, Any]:
        try:
            now = datetime.now(timezone.utc).isoformat()
            healthy = self._initialized and self._error_count < 10
            self._health = {
                "healthy": healthy,
                "last_check": now,
                "error": None if healthy else "error threshold exceeded",
                "initialized": self._initialized,
                "request_count": self._request_count,
                "error_count": self._error_count,
                "enabled": self.enabled,
            }
            return dict(self._health)
        except Exception as exc:  # noqa: BLE001
            return {"healthy": False, "error": str(exc), "last_check": datetime.now(timezone.utc).isoformat()}

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    async def lookup_url(self, url: str) -> Optional[ThreatIndicator]:
        if hasattr(url, "ioc"):
            url = getattr(url, "ioc")
        if not isinstance(url, str):
            return None
        self._ensure_initialized()
        if not self.enabled:
            return None
        url = sanitize_url(url)
        valid, err = validate_lookup_input(url, "url")
        if not valid:
            logger.debug("PhishTank lookup_url invalid: %s", err)
            return None
        self._request_count += 1
        try:
            req = PhishTankRequest(url=url)
            response = await self._client.check_url(req, ttl=self.ttl)
            return response_to_indicator(response, ttl=self.ttl)
        except ValueError:
            return None
        except Exception as exc:  # noqa: BLE001
            self._error_count += 1
            logger.warning("PhishTank lookup_url failed for %s: %s", url, exc)
            return None

    async def lookup_domain(self, domain: str) -> Optional[ThreatIndicator]:
        if hasattr(domain, "ioc"):
            domain = getattr(domain, "ioc")
        logger.debug("PhishTank: domain lookup not primary -> None")
        return None

    async def lookup_ip(self, ip: str) -> Optional[ThreatIndicator]:
        if hasattr(ip, "ioc"):
            ip = getattr(ip, "ioc")
        logger.debug("PhishTank: IP lookup not supported")
        return None

    async def lookup_hash(self, hash_value: str) -> Optional[ThreatIndicator]:
        if hasattr(hash_value, "ioc"):
            hash_value = getattr(hash_value, "ioc")
        logger.debug("PhishTank: hash lookup not supported")
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
    def from_dict(cls, data: Dict[str, Any]) -> "PhishTankProvider":
        return cls(
            api_key=data.get("api_key"),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ("name", "version", "api_key", "enabled")},
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
