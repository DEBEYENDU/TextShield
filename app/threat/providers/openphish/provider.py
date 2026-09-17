from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.threat.ioc.models import IOCType
from app.threat.providers.threat_indicator import ThreatIndicator

from .client import OpenPhishClient
from .config import OpenPhishConfig
from .mapper import response_to_indicator
from .models import OpenPhishRequest
from .validator import validate_lookup_input, sanitize_url

logger = logging.getLogger(__name__)


class OpenPhishProvider:
    """OpenPhish threat intelligence provider.

    Capabilities: URL reputation (phishing feed). Gracefully degrades when
    feed unavailable; respects rate limits; integrates with retry and cache
    via internal client. Returns normalized ThreatIndicator; provider-specific
    OpenPhishResponse never leaves the provider layer.
    """

    name = "openphish"
    version = "1.0.0"

    def __init__(self, api_key: Optional[str] = None, enabled: bool = True, **kwargs: Any):
        self._api_key = api_key
        self._enabled = enabled
        self._initialized = False
        self._config = OpenPhishConfig(api_key=api_key or "", enabled=enabled, **kwargs)
        self.ttl: int = self._config.ttl
        self.timeout: float = self._config.timeout
        self.configuration: Dict[str, Any] = self._config.to_dict()
        self._client = OpenPhishClient(
            feed_url=self._config.feed_url,
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            backoff_factor=self._config.backoff_factor,
            rate_limit_per_minute=self._config.rate_limit_per_minute,
        )
        self._health: Dict[str, Any] = {"healthy": True, "last_check": None, "error": None}
        self._request_count: int = 0
        self._error_count: int = 0

    # ------------------------------------------------------------------ properties
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
            "feed_url": self._config.feed_url,
            "rate_limit_per_minute": self._config.rate_limit_per_minute,
            "max_retries": self._config.max_retries,
        }

    def capabilities(self) -> List[str]:
        return ["url_reputation", "phishing_detection", "feed_intelligence"]

    # ------------------------------------------------------------------ lifecycle
    def initialize(self) -> None:
        self._initialized = True
        self._health = {"healthy": True, "last_check": datetime.now(timezone.utc).isoformat(), "error": None}
        logger.info("OpenPhish provider initialized: enabled=%s", self.enabled)

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("OpenPhish provider shut down")

    def health_check(self) -> Dict[str, Any]:
        try:
            now = datetime.now(timezone.utc).isoformat()
            # Basic health: initialized and not error overloaded
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

    # ------------------------------------------------------------------ helpers
    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def _handle_disabled(self) -> None:
        if not self.enabled:
            logger.debug("OpenPhish: provider disabled, skipping lookup")

    # ------------------------------------------------------------------ lookups
    async def lookup_url(self, url: str) -> Optional[ThreatIndicator]:
        """Look up a URL for phishing reputation."""
        # Support both string and LookupRequest-like object for engine compatibility
        if hasattr(url, "ioc"):
            url = getattr(url, "ioc")  # LookupRequest
        if not isinstance(url, str):
            return None
        self._ensure_initialized()
        if not self.enabled:
            return None
        url = sanitize_url(url)
        valid, err = validate_lookup_input(url, "url")
        if not valid:
            logger.debug("OpenPhish lookup_url invalid input: %s", err)
            return None
        self._request_count += 1
        try:
            # OpenPhish is open feed: no API key required
            req = OpenPhishRequest(url=url)
            # Use retry via client; gracefully degrade on failure
            response = await self._client.check_url(req, ttl=self.ttl)
            indicator = response_to_indicator(response, ttl=self.ttl)
            if indicator is None:
                return None
            # Attach ttl as timedelta if needed
            return indicator
        except ValueError:
            return None
        except Exception as exc:  # noqa: BLE001
            self._error_count += 1
            logger.warning("OpenPhish lookup_url failed for %s: %s", url, exc)
            return None  # graceful degradation

    async def lookup_domain(self, domain: str) -> Optional[ThreatIndicator]:
        if hasattr(domain, "ioc"):
            domain = getattr(domain, "ioc")
        # OpenPhish primarily supports URL; domain lookup not primary -> return None gracefully
        logger.debug("OpenPhish: domain lookup not primary capability, returning None")
        return None

    async def lookup_ip(self, ip: str) -> Optional[ThreatIndicator]:
        if hasattr(ip, "ioc"):
            ip = getattr(ip, "ioc")
        logger.debug("OpenPhish: IP lookup not supported, returning None")
        return None

    async def lookup_hash(self, hash_value: str) -> Optional[ThreatIndicator]:
        if hasattr(hash_value, "ioc"):
            hash_value = getattr(hash_value, "ioc")
        logger.debug("OpenPhish: hash lookup not supported")
        return None

    # ------------------------------------------------------------------ serialization
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
    def from_dict(cls, data: Dict[str, Any]) -> "OpenPhishProvider":
        return cls(
            api_key=data.get("api_key"),
            enabled=data.get("enabled", True),
            **{k: v for k, v in data.items() if k not in ("name", "version", "api_key", "enabled")},
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
