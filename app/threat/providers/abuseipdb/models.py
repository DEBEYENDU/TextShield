from __future__ import annotations

from typing import Any, Dict, List, Optional


class AbuseIPDBRequest:
    """Request model for AbuseIPDB lookup."""

    def __init__(self, ip_address: str, max_age_days: int = 30, verbose: bool = False):
        self.ip_address = ip_address
        self.max_age_days = max_age_days
        self.verbose = verbose


class AbuseIPDBResponse:
    """Response model from AbuseIPDB API.

    Mimics AbuseIPDB check endpoint:
      data: { ipAddress, isWhitelisted, abuseConfidenceScore (0-100),
              totalReports, numDistinctUsers, lastReportedAt, countryCode, domain, ...}
    """

    def __init__(
        self,
        ip_address: str,
        abuse_confidence_score: int = 0,
        is_whitelisted: bool = False,
        total_reports: int = 0,
        num_distinct_users: int = 0,
        last_reported_at: Optional[str] = None,
        country_code: Optional[str] = None,
        domain: Optional[str] = None,
        hostnames: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.ip_address = ip_address
        self.abuse_confidence_score = int(abuse_confidence_score)
        self.is_whitelisted = is_whitelisted
        self.total_reports = total_reports
        self.num_distinct_users = num_distinct_users
        self.last_reported_at = last_reported_at
        self.country_code = country_code
        self.domain = domain
        self.hostnames = hostnames or []
        self.metadata = metadata or {}

    @property
    def is_malicious(self) -> bool:
        # Whitelisted never malicious; threshold default 25
        if self.is_whitelisted:
            return False
        return self.abuse_confidence_score >= 25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "abuse_confidence_score": self.abuse_confidence_score,
            "is_whitelisted": self.is_whitelisted,
            "total_reports": self.total_reports,
            "num_distinct_users": self.num_distinct_users,
            "last_reported_at": self.last_reported_at,
            "country_code": self.country_code,
            "domain": self.domain,
            "hostnames": self.hostnames,
            "metadata": self.metadata,
            "is_malicious": self.is_malicious,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbuseIPDBResponse":
        return cls(
            ip_address=data.get("ip_address", data.get("ipAddress", "")),
            abuse_confidence_score=data.get("abuse_confidence_score", data.get("abuseConfidenceScore", 0)),
            is_whitelisted=data.get("is_whitelisted", data.get("isWhitelisted", False)),
            total_reports=data.get("total_reports", data.get("totalReports", 0)),
            num_distinct_users=data.get("num_distinct_users", data.get("numDistinctUsers", 0)),
            last_reported_at=data.get("last_reported_at", data.get("lastReportedAt")),
            country_code=data.get("country_code", data.get("countryCode")),
            domain=data.get("domain"),
            hostnames=data.get("hostnames", []),
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
