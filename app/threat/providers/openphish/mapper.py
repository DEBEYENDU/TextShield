from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.threat.providers.threat_indicator import ThreatIndicator
from app.threat.ioc.models import IOCType

try:
    from app.threat.execution.models import ThreatEvidence  # type: ignore
except Exception:  # fallback if execution model not available
    ThreatEvidence = None  # type: ignore

from .models import OpenPhishResponse


def response_to_indicator(response: OpenPhishResponse, ttl: int = 3600) -> Optional[ThreatIndicator]:
    """Map OpenPhishResponse -> ThreatIndicator.
    
    Provider-specific response objects must never leave the provider layer;
    callers should use the returned ThreatIndicator or the evidence mapper below.
    """
    if response is None:
        return None
    if not response.is_phishing:
        return None

    confidence = float(response.confidence) if response.confidence else 0.88
    # Map confidence to severity
    if confidence >= 0.85:
        severity = "high"
    elif confidence >= 0.6:
        severity = "medium"
    else:
        severity = "low"

    return ThreatIndicator(
        indicator=response.url,
        indicator_type=IOCType.URL,
        provider="openphish",
        detection_status="phishing",
        confidence=confidence,
        severity=severity,
        timestamp=datetime.now(timezone.utc),
        ttl=timedelta(seconds=ttl),
        source="openphish",
        explanation=f"OpenPhish: URL flagged as phishing (confidence {confidence:.2f})",
    )


def indicator_to_evidence(indicator: object, ttl: int = 3600) -> Any:
    """Normalize a ThreatIndicator (or dict) into the internal ThreatEvidence model."""
    if indicator is None:
        return None

    # Extract fields from ThreatIndicator or dict
    if hasattr(indicator, "indicator"):
        ind = getattr(indicator, "indicator")
        raw_type = getattr(indicator, "indicator_type", IOCType.URL)
        ioc_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
        threat_status = getattr(indicator, "detection_status", "unknown")
        confidence = float(getattr(indicator, "confidence", 0.0))
        severity = getattr(indicator, "severity", "unknown")
        source = getattr(indicator, "source", "openphish")
        explanation = getattr(indicator, "explanation", "")
        ttl_val = getattr(indicator, "ttl", None)
        if hasattr(ttl_val, "total_seconds"):
            ttl = int(ttl_val.total_seconds())
    else:
        # dict fallback
        d = indicator if isinstance(indicator, dict) else {}
        ind = d.get("indicator", "")
        ioc_type = d.get("indicator_type", "url")
        threat_status = d.get("detection_status", "unknown")
        confidence = float(d.get("confidence", 0.0))
        severity = d.get("severity", "unknown")
        source = d.get("source", "openphish")
        explanation = d.get("explanation", "")
        ttl = int(d.get("ttl", ttl) or ttl)

    ioc_type_map = {
        "url": "url", "domain": "domain", "ipv4": "ipv4", "ipv6": "ipv6",
        "ip": "ip", "email": "email", "phone": "phone",
        "crypto_wallet": "crypto_wallet", "qr_code_url": "qr_code_url",
        "url_shortener": "url_shortener",
    }
    mapped_ioc = ioc_type_map.get(str(ioc_type).lower(), "url")

    # Prefer importing the canonical ThreatEvidence from execution if available
    try:
        from app.threat.execution.models import ThreatEvidence as ExecEvidence  # type: ignore
        # execution ThreatEvidence may be dataclass; attempt to construct generically
        return ExecEvidence(
            indicator=ind,
            ioc_type=mapped_ioc,
            threat_status=threat_status,
            confidence=confidence,
            severity=severity,
            source=source,
            explanation=explanation,
            ttl=int(ttl),
            metadata={"provider": "openphish"},
        )
    except Exception:
        pass

    # Fallback: return dict shaped like evidence
    return {
        "indicator": ind,
        "ioc_type": mapped_ioc,
        "threat_status": threat_status,
        "confidence": confidence,
        "severity": severity,
        "source": source,
        "explanation": explanation,
        "ttl": int(ttl),
        "metadata": {"provider": "openphish"},
    }


def response_to_evidence(response: OpenPhishResponse, ttl: int = 3600) -> Any:
    """Direct mapping Response -> Evidence (composes response_to_indicator + indicator_to_evidence)."""
    indicator = response_to_indicator(response, ttl=ttl)
    if indicator is None:
        return None
    return indicator_to_evidence(indicator, ttl=ttl)
