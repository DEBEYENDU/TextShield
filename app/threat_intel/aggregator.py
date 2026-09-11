"""Threat-intel aggregation: merge provider verdicts without hiding
disagreement. known_malicious anywhere (from a successful lookup) sets
HIGH; otherwise weighted scoring over reliability × freshness × agreement.
UNKNOWN never counts as safe.
"""

from __future__ import annotations

from app.threat_intel.models import ProviderResult

_VERDICT_SCORE = {"known_malicious": 1.0, "suspicious": 0.6, "unknown": 0.0,
                  "benign": -0.6, "unavailable": 0.0, "unsupported": 0.0}

# Static reliability per provider family (multiplied by result confidence).
RELIABILITY = {"google_safe_browsing": 0.95, "virustotal": 0.9,
               "mock": 0.5, "static": 0.7, "local": 0.8}


def aggregate(ioc: str, ioc_type: str,
              results: list[ProviderResult]) -> dict:
    """Combine results; preserve every individual verdict."""
    usable = [r for r in results
              if r.verdict not in {"unavailable", "unsupported"}]
    if not usable:
        return {"ioc": ioc, "ioc_type": ioc_type,
                "aggregated_verdict": "unknown", "threat_level": "UNKNOWN",
                "confidence": 0.0, "agreement": 0.0,
                "results": [r.to_dict() for r in results],
                "disagreement": False,
                "reason": "no provider returned a usable verdict"}
    malicious = [r for r in usable if r.verdict == "known_malicious"]
    if malicious:
        best = max(malicious,
                   key=lambda r: r.confidence * RELIABILITY.get(r.provider, 0.5))
        return {"ioc": ioc, "ioc_type": ioc_type,
                "aggregated_verdict": "known_malicious", "threat_level": "HIGH",
                "confidence": round(best.confidence, 3),
                "agreement": round(len(malicious) / len(usable), 3),
                "results": [r.to_dict() for r in results],
                "disagreement": any(r.verdict in {"benign", "unknown"} for r in usable),
                "reason": f"flagged malicious by {best.provider}"}
    score = 0.0
    weight = 0.0
    for result in usable:
        reliability = RELIABILITY.get(result.provider, 0.5)
        w = reliability * (0.5 + result.confidence)
        score += _VERDICT_SCORE.get(result.verdict, 0.0) * w
        weight += w
    normalized = score / weight if weight else 0.0
    if normalized >= 0.45:
        verdict, level = "suspicious", "MEDIUM"
    elif normalized <= -0.3:
        verdict, level = "benign", "LOW"
    else:
        verdict, level = "unknown", "UNKNOWN"
    verdicts = {r.verdict for r in usable}
    return {"ioc": ioc, "ioc_type": ioc_type,
            "aggregated_verdict": verdict, "threat_level": level,
            "confidence": round(min(abs(normalized), 1.0), 3),
            "agreement": round(1.0 - len(verdicts - {"unknown"}) / max(len(usable), 1), 3)
            if len(verdicts) > 1 else 1.0,
            "results": [r.to_dict() for r in results],
            "disagreement": len(verdicts - {"unknown"}) > 1,
            "reason": f"weighted score {normalized:.2f} over {len(usable)} providers"}
