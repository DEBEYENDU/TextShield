from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timezone


class GoogleSafeBrowsingRequest:
    """Request model for Google Safe Browsing lookup."""
    def __init__(self, url: str, domain: Optional[str] = None, ip: Optional[str] = None):
        self.url = url
        self.domain = domain
        self.ip = ip


class GoogleSafeBrowsingResponse:
    """Response model from Google Safe Browsing."""
    def __init__(self,
                 threat_types: Optional[list] = None,
                 platform_types: Optional[list] = None,
                 threat_entry_type: Optional[str] = None,
                 threat_entry: Optional[Dict] = None,
                 violation_types: Optional[list] = None):
        self.threat_types = threat_types or []
        self.platform_types = platform_types or []
        self.threat_entry_type = threat_entry_type
        self.threat_entry = threat_entry or {}
        self.violation_types = violation_types or []


class ThreatEvidence:
    """Normalized evidence model used internally by TextShield."""
    def __init__(self,
                 indicator: str,
                 ioc_type: str,
                 threat_status: str,
                 confidence: float,
                 severity: str,
                 source: str,
                 explanation: str,
                 ttl: int,
                 metadata: Optional[Dict[str, Any]] = None):
        self.indicator = indicator
        self.ioc_type = ioc_type
        self.threat_status = threat_status
        self.confidence = confidence
        self.severity = severity
        self.source = source
        self.explanation = explanation
        self.ttl = ttl
        self.metadata = metadata or {}