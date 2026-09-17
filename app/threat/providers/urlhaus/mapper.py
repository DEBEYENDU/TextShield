from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.threat.ioc.models import IOCType
from app.threat.providers.threat_indicator import ThreatIndicator

from .models import URLhausResponse


def response_to_indicator(response: URLhausResponse, ttl: int = 600) -> Any:
    if response is None:
        return None
    if not response.is_malicious:
        return None

    confidence = float(response.confidence or 0.91)
    threat = (response.threat or "malware_download").lower()
    if threat in ("ransomware", "trojan", "stealer"):
        severity = "critical"
    elif threat in ("malware_download", "malware"):
        severity = "high"
    else:
        severity = "medium"

    explanation = f"URLhaus: Malware URL detected (threat={threat}, confidence {confidence:.2f})"
    if response.payloads:
        payload_info = ", ".join(p.get("signature", "unknown") for p in response.payloads[:2])
        explanation += f" payloads: {payload_info}"

    return ThreatIndicator(
        indicator=response.url,
        indicator_type=IOCType.URL,
        provider="urlhaus",
        detection_status="malware",
        confidence=confidence,
        severity=severity,
        timestamp=datetime.now(timezone.utc),
        ttl=timedelta(seconds=ttl),
        source="urlhaus",
        explanation=explanation,
    )


def indicator_to_evidence(indicator: Any, ttl: int = 600) -> Any:
    if indicator is None:
        return None
    if hasattr(indicator, "indicator"):
        ind = getattr(indicator, "indicator")
        raw_type = getattr(indicator, "indicator_type", IOCType.URL)
        ioc_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
        threat_status = getattr(indicator, "detection_status", "unknown")
        confidence = float(getattr(indicator, "confidence", 0.0))
        severity = getattr(indicator, "severity", "unknown")
        source = getattr(indicator, "source", "urlhaus")
        explanation = getattr(indicator, "explanation", "")
        ttl_val = getattr(indicator, "ttl", None)
        if hasattr(ttl_val, "total_seconds"):
            ttl = int(ttl_val.total_seconds())
    else:
        d = indicator if isinstance(indicator, dict) else {}
        ind = d.get("indicator", "")
        ioc_type = d.get("indicator_type", "url")
        threat_status = d.get("detection_status", "unknown")
        confidence = float(d.get("confidence", 0.0))
        severity = d.get("severity", "unknown")
        source = d.get("source", "urlhaus")
        explanation = d.get("explanation", "")
        ttl = int(d.get("ttl", ttl) or ttl)

    ioc_type_map = {
        "url": "url", "domain": "domain", "ipv4": "ipv4", "ipv6": "ipv6",
        "ip": "ip", "email": "email", "phone": "phone",
        "crypto_wallet": "crypto_wallet", "qr_code_url": "qr_code_url",
        "url_shortener": "url_shortener",
    }
    mapped = ioc_type_map.get(str(ioc_type).lower(), "url")
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
            metadata={"provider": "urlhaus"},
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
            "metadata": {"provider": "urlhaus"},
        }


def response_to_evidence(response: URLhausResponse, ttl: int = 600) -> Any:
    ind = response_to_indicator(response, ttl=ttl)
    if ind is None:
        return None
    return indicator_to_evidence(ind, ttl=ttl)
