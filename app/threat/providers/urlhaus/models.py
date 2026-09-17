from __future__ import annotations

from typing import Any, Dict, List, Optional


class URLhausRequest:
    """Request model for URLhaus lookup."""

    def __init__(self, url: str):
        self.url = url


class URLhausResponse:
    """Response model from URLhaus API.

    Fields mimic https://urlhaus-api.abuse.ch/ :
      query_status: 'ok' | 'no_results' | etc
      threat, blacklists, payloads, tags, url_status
    """

    def __init__(
        self,
        url: str,
        query_status: str = "no_results",
        threat: Optional[str] = None,
        blacklists: Optional[Dict[str, str]] = None,
        payloads: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        url_status: Optional[str] = None,
        date_added: Optional[str] = None,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.query_status = query_status
        self.threat = threat
        self.blacklists = blacklists or {}
        self.payloads = payloads or []
        self.tags = tags or []
        self.url_status = url_status
        self.date_added = date_added
        self.confidence = confidence
        self.metadata = metadata or {}

    @property
    def is_malicious(self) -> bool:
        return self.query_status == "ok" and self.threat is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "query_status": self.query_status,
            "threat": self.threat,
            "blacklists": self.blacklists,
            "payloads": self.payloads,
            "tags": self.tags,
            "url_status": self.url_status,
            "date_added": self.date_added,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "is_malicious": self.is_malicious,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "URLhausResponse":
        return cls(
            url=data.get("url", ""),
            query_status=data.get("query_status", "no_results"),
            threat=data.get("threat"),
            blacklists=data.get("blacklists", {}),
            payloads=data.get("payloads", []),
            tags=data.get("tags", []),
            url_status=data.get("url_status"),
            date_added=data.get("date_added"),
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {}),
        )


class ThreatEvidence:
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
