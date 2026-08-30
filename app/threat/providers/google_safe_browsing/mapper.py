from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.threat.execution.models import ThreatEvidence
from app.threat.ioc.models import IOCType


def indicator_to_evidence(indicator: object) -> ThreatEvidence:
    """Normalize a ThreatIndicator (or dict) into the internal ThreatEvidence model."""
    if hasattr(indicator, "indicator"):
        ind = indicator.indicator
        ioc_type = indicator.indicator_type.value if hasattr(indicator.indicator_type, "value") else str(indicator.indicator_type)
        threat_status = indicator.detection_status
        confidence = indicator.confidence
        severity = indicator.severity
        source = indicator.source
        explanation = indicator.explanation
        ttl = indicator.ttl.total_seconds() if indicator.ttl else 3600
    else:
        # dict fallback
        ind = indicator.get("indicator", "")
        ioc_type = indicator.get("indicator_type", "url")
        threat_status = indicator.get("detection_status", "unknown")
        confidence = indicator.get("confidence", 0.0)
        severity = indicator.get("severity", "unknown")
        source = indicator.get("source", "")
        explanation = indicator.get("explanation", "")
        ttl = indicator.get("ttl", 3600)

    # Map IOCType string to our enum-compatible string
    ioc_type_map = {
        "url": "url", "domain": "domain", "ipv4": "ipv4", "ipv6": "ipv6",
        "ip": "ip", "email": "email", "phone": "phone",
        "crypto_wallet": "crypto_wallet", "qr_code_url": "qr_code_url",
        "url_shortener": "url_shortener"
    }
    mapped_ioc = ioc_type_map.get(ioc_type.lower(), "url")

    return ThreatEvidence(
        indicator=ind,
        ioc_type=mapped_ioc,
        threat_status=threat_status,
        confidence=confidence,
        severity=severity,
        source=source,
        explanation=explanation,
        ttl=int(ttl),
        metadata={}
    )