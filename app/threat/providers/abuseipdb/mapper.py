from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.threat.ioc.models import IOCType
from app.threat.providers.threat_indicator import ThreatIndicator

from .models import AbuseIPDBResponse


def response_to_indicator(response: AbuseIPDBResponse, ttl: int = 900) -> Any:
    if response is None:
        return None
    if not response.is_malicious:
        return None

    score = int(response.abuse_confidence_score)
    confidence = min(score / 100.0, 0.99)
    # Map abuse score to severity per AbuseIPDB guidance
    if score >= 75:
        severity = "critical"
    elif score >= 50:
        severity = "high"
    elif score >= 25:
        severity = "medium"
    else:
        severity = "low"

    # Determine IOC type strictly ipv4 / ipv6
    ioc_type = IOCType.IPV6 if ":" in response.ip_address else IOCType.IPV4

    explanation = (
        f"AbuseIPDB: IP {response.ip_address} has abuse confidence {score}% "
        f"({response.total_reports} reports from {response.num_distinct_users} users)"
    )
    if response.is_whitelisted:
        explanation += " [whitelisted]"

    detection = "malicious" if score >= 25 else "suspicious"

    return ThreatIndicator(
        indicator=response.ip_address,
        indicator_type=ioc_type,
        provider="abuseipdb",
        detection_status=detection,
        confidence=confidence,
        severity=severity,
        timestamp=datetime.now(timezone.utc),
        ttl=timedelta(seconds=ttl),
        source="abuseipdb",
        explanation=explanation,
    )


def indicator_to_evidence(indicator: Any, ttl: int = 900) -> Any:
    if indicator is None:
        return None
    if hasattr(indicator, "indicator"):
        ind = getattr(indicator, "indicator")
        raw_type = getattr(indicator, "indicator_type", IOCType.IPV4)
        ioc_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
        threat_status = getattr(indicator, "detection_status", "unknown")
        confidence = float(getattr(indicator, "confidence", 0.0))
        severity = getattr(indicator, "severity", "unknown")
        source = getattr(indicator, "source", "abuseipdb")
        explanation = getattr(indicator, "explanation", "")
        ttl_val = getattr(indicator, "ttl", None)
        if hasattr(ttl_val, "total_seconds"):
            ttl = int(ttl_val.total_seconds())
    else:
        d = indicator if isinstance(indicator, dict) else {}
        ind = d.get("indicator", "")
        ioc_type = d.get("indicator_type", "ipv4")
        threat_status = d.get("detection_status", "unknown")
        confidence = float(d.get("confidence", 0.0))
        severity = d.get("severity", "unknown")
        source = d.get("source", "abuseipdb")
        explanation = d.get("explanation", "")
        ttl = int(d.get("ttl", ttl) or ttl)

    ioc_type_map = {
        "url": "url", "domain": "domain", "ipv4": "ipv4", "ipv6": "ipv6",
        "ip": "ip", "email": "email", "phone": "phone",
        "crypto_wallet": "crypto_wallet", "qr_code_url": "qr_code_url",
        "url_shortener": "url_shortener",
    }
    mapped = ioc_type_map.get(str(ioc_type).lower(), "ipv4")
    try:
        from app.threat.execution.models import ThreatEvidence as ExecEvidence  # type: ignore
        return ExecEvidence(
            indicator=ind,
            ioc_type=mapped,
            threat_status=threat_status,
            confidence=confidence,
            severity=severity,
            source=source,
            explanation=explanation,
            ttl=int(ttl),
            metadata={"provider": "abuseipdb"},
        )
    except Exception:
        return {
            "indicator": ind,
            "ioc_type": mapped,
            "threat_status": threat_status,
            "confidence": confidence,
            "severity": severity,
            "source": source,
            "explanation": explanation,
            "ttl": int(ttl),
            "metadata": {"provider": "abuseipdb"},
        }


def response_to_evidence(response: AbuseIPDBResponse, ttl: int = 900) -> Any:
    ind = response_to_indicator(response, ttl=ttl)
    if ind is None:
        return None
    return indicator_to_evidence(ind, ttl=ttl)
