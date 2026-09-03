from __future__ import annotations

from typing import Any, Dict, Optional


class PhishTankRequest:
    """Request model for PhishTank lookup."""

    def __init__(self, url: str, domain: Optional[str] = None):
        self.url = url
        self.domain = domain


class PhishTankResponse:
    """Response model from PhishTank API.

    Canonical fields:
      - in_database: whether URL is in PhishTank DB
      - verified: whether entry is verified
      - valid: whether phishing is valid
      - phish_id, phish_detail_url, submission_time, verification_time
    """

    def __init__(
        self,
        url: str,
        in_database: bool = False,
        verified: bool = False,
        valid: bool = False,
        phish_id: Optional[str] = None,
        phish_detail_url: Optional[str] = None,
        submission_time: Optional[str] = None,
        verification_time: Optional[str] = None,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.in_database = in_database
        self.verified = verified
        self.valid = valid
        self.phish_id = phish_id
        self.phish_detail_url = phish_detail_url
        self.submission_time = submission_time
        self.verification_time = verification_time
        self.confidence = confidence
        self.metadata = metadata or {}

    @property
    def is_phishing(self) -> bool:
        return self.in_database and self.valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "in_database": self.in_database,
            "verified": self.verified,
            "valid": self.valid,
            "phish_id": self.phish_id,
            "phish_detail_url": self.phish_detail_url,
            "submission_time": self.submission_time,
            "verification_time": self.verification_time,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "is_phishing": self.is_phishing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhishTankResponse":
        return cls(
            url=data.get("url", ""),
            in_database=data.get("in_database", False),
            verified=data.get("verified", False),
            valid=data.get("valid", False),
            phish_id=data.get("phish_id"),
            phish_detail_url=data.get("phish_detail_url"),
            submission_time=data.get("submission_time"),
            verification_time=data.get("verification_time"),
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {}),
        )


class ThreatEvidence:
    """Normalized evidence model."""

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
