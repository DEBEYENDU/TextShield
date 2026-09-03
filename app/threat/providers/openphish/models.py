from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class OpenPhishRequest:
    """Request model for OpenPhish lookup."""

    def __init__(self, url: str, domain: Optional[str] = None):
        self.url = url
        self.domain = domain


class OpenPhishResponse:
    """Response model from OpenPhish feed/API."""

    def __init__(
        self,
        url: str,
        is_phishing: bool = False,
        feed_source: str = "openphish",
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.is_phishing = is_phishing
        self.feed_source = feed_source
        self.confidence = confidence
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "is_phishing": self.is_phishing,
            "feed_source": self.feed_source,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpenPhishResponse":
        return cls(
            url=data.get("url", ""),
            is_phishing=data.get("is_phishing", False),
            feed_source=data.get("feed_source", "openphish"),
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {}),
        )


class ThreatEvidence:
    """Normalized evidence model used internally by TextShield."""

    def __init__(
        self,
        indicator: str,
        ioc_type: str,
        threat_status: str,
        confidence: float,
        severity: str,
        source: str,
        explanation: str,
        ttl: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.indicator = indicator
        self.ioc_type = ioc_type
        self.threat_status = threat_status
        self.confidence = confidence
        self.severity = severity
        self.source = source
        self.explanation = explanation
        self.ttl = ttl
        self.metadata = metadata or {}
