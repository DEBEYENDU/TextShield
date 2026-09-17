from __future__ import annotations

import abc
import asyncio
import json
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from app.threat.ioc.models import IOCType, ExtractedIOC
    IOCExtractor = None  # type: ignore
except Exception:
    IOCType = None  # type: ignore
    ExtractedIOC = None  # type: ignore
    IOCExtractor = None  # type: ignore

logger = logging.getLogger(__name__)


class ThreatIntelligenceError(Exception):
    """Base exception for all threat intelligence errors."""
    pass


class ProviderNotAvailableError(ThreatIntelligenceError):
    """Raised when a provider is unavailable."""
    pass


class ProviderRateLimitError(ThreatIntelligenceError):
    """Raised when provider rate limit is exceeded."""
    pass


class ProviderTimeoutError(ThreatIntelligenceError):
    """Raised when provider request times out."""
    pass


class ProviderConfigError(ThreatIntelligenceError):
    """Raised when provider configuration is invalid."""
    pass


@abc.abstractmethod
class ThreatProviderABC(abc.ABC):
    """Abstract base class for all threat intelligence providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the provider version."""
        pass
    
    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Return whether the provider is enabled."""
        pass
    
    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool) -> None:
        """Enable or disable the provider."""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return provider metadata (capabilities, TTL, etc.)."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider (load config, establish connections)."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the provider cleanly."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check provider health status."""
        pass
    
    @abstractmethod
    async def lookup_url(self, url: str) -> Optional["ThreatIndicator"]:
        """Look up a URL for threat intelligence."""
        pass
    
    @abstractmethod
    async def lookup_domain(self, domain: str) -> Optional["ThreatIndicator"]:
        """Look up a domain for threat intelligence."""
        pass
    
    @abstractmethod
    async def lookup_ip(self, ip: str) -> Optional["ThreatIndicator"]:
        """Look up an IP address for threat intelligence."""
        pass
    
    @abstractmethod
    async def lookup_hash(self, hash_value: str) -> Optional["ThreatIndicator"]:
        """Look up a hash for threat intelligence (future-compatible)."""
        pass


@dataclass
class ThreatIndicator:
    """Structured threat intelligence indicator."""
    
    indicator: str
    indicator_type: IOCType
    provider: str
    detection_status: str  # "malicious", "benign", "unknown", "phishing", "malware", etc.
    confidence: float  # 0.0 to 1.0
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    ttl: Optional[timedelta]  # Time to live for the result
    source: str  # e.g., "google_safe_browsing", "virustotal"
    explanation: str  # Human-readable explanation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "indicator_type": self.indicator_type.value,
            "provider": self.provider,
            "detection_status": self.detection_status,
            "confidence": self.confidence,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl.total_seconds() if self.ttl else None,
            "source": self.source,
            "explanation": self.explanation,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatIndicator":
        from datetime import datetime
        return cls(
            indicator=data["indicator"],
            indicator_type=IOCType(data["indicator_type"]),
            provider=data["provider"],
            detection_status=data["detection_status"],
            confidence=data["confidence"],
            severity=data["severity"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=timedelta(seconds=data["ttl_seconds"]) if data.get("ttl_seconds") else None,
            source=data.get("source", ""),
            explanation=data.get("explanation", ""),
        )


class ProviderRegistry:
    """Registry for managing all threat intelligence providers."""
    
    def __init__(self):
        self._providers: Dict[str, ThreatProviderABC] = {}
        self._provider_config: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, provider: ThreatProviderABC, config: Optional[Dict[str, Any]] = None) -> None:
        """Register a provider."""
        self._providers[name] = provider
        if config:
            self._provider_config[name] = config
        logger.info(f"Provider registered: {name}")
    
    def unregister(self, name: str) -> None:
        """Unregister a provider."""
        if name in self._providers:
            del self._providers[name]
            if name in self._provider_config:
                del self._provider_config[name]
            logger.info(f"Provider unregistered: {name}")
    
    def get(self, name: str) -> Optional[ThreatProviderABC]:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def get_all(self) -> Dict[str, ThreatProviderABC]:
        """Get all registered providers."""
        return dict(self._providers)
    
    def get_enabled(self) -> Dict[str, ThreatProviderABC]:
        """Get all enabled providers."""
        return {
            name: provider
            for name, provider in self._providers.items()
            if provider.enabled
        }
    
    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all providers."""
        return {
            name: provider.metadata
            for name, provider in self._providers.items()
        }
    
    def initialize_all(self) -> None:
        """Initialize all registered providers."""
        for name, provider in self._providers.items():
            try:
                provider.initialize()
                logger.info(f"Provider initialized: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {name}: {e}")
    
    def shutdown_all(self) -> None:
        """Shut down all registered providers."""
        for name, provider in self._providers.items():
            try:
                provider.shutdown()
                logger.info(f"Provider shut down: {name}")
            except Exception as e:
                logger.error(f"Failed to shut down provider {name}: {e}")
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = provider.health_check()
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}
        return results


# Global registry instance
_threat_registry: Optional[ProviderRegistry] = None


def get_threat_registry() -> ProviderRegistry:
    """Get the global threat provider registry."""
    global _threat_registry
    if _threat_registry is None:
        _threat_registry = ProviderRegistry()
    return _threat_registry


def init_threat_system() -> ProviderRegistry:
    """Initialize the complete threat intelligence system."""
    registry = get_threat_registry()
    return registry