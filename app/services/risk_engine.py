"""Risk engine.

Risk is scored on a 0-100 scale and mapped to LOW / MEDIUM / HIGH.

Inputs (all transparent and logged as ``risk_factors``):

* ML classification + confidence
* detected indicators (severity-weighted)
* URL pattern warnings
* RAG evidence pointing at high-risk knowledge categories

Weights are defined in ``app/core/config.py`` so the logic is
configurable. Informational only - not legal, financial or security
authority.
"""
from __future__ import annotations

from app.core.config import settings


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _level(score: float) -> str:
    if score >= settings.RISK_HIGH_THRESHOLD:
        return "HIGH"
    if score >= settings.RISK_MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


HIGH_RISK_CATEGORIES = {"banking_scams", "phishing", "investment_scams"}


def compute_risk(
    classification: str,
    confidence: float,
    indicators: list[dict],
    urls: list[dict],
    rag_evidence: list[dict],
) -> dict:
    """Compute the risk level and the factors that produced it."""
    factors: list[str] = []
    score = (
        settings.RISK_SPAM_BASE if classification == "SPAM" else settings.RISK_HAM_BASE
    )
    factors.append(
        f"ML classified the message as {classification} "
        f"(confidence {confidence * 100:.0f}%)"
    )

    # indicator weights
    for indicator in indicators:
        severity = indicator.get("severity", "low")
        weight = settings.RISK_INDICATOR_WEIGHTS.get(severity, 0.0)
        score += weight
        factors.append(
            f"Indicator '{indicator.get('indicator')}' ({severity})"
        )

    # URL flags
    flagged = [u for u in urls if u.get("warnings")]
    for url in flagged:
        if url.get("has_ip_host"):
            score += settings.RISK_URL_HIGH_PATTERN
            factors.append(f"URL {url.get('url', '')[:40]} uses a raw IP host")
        if url.get("suspicious_tld"):
            score += settings.RISK_URL_SUSPICIOUS
            factors.append(f"URL {url.get('url', '')[:40]} uses a suspicious TLD")
        if url.get("is_shortened"):
            score += settings.RISK_URL_SHORTENER
            factors.append(f"URL {url.get('url', '')[:40]} is shortened")
        if url.get("suspicious_chars"):
            score += settings.RISK_URL_HIGH_PATTERN
            factors.append(f"URL {url.get('url', '')[:40]} contains suspicious characters")

    # confidence adjustment
    if classification == "SPAM" and confidence >= 0.8:
        score += settings.RISK_HIGH_CONF_BONUS
        factors.append(f"High model confidence ({confidence * 100:.0f}%) in the SPAM result")
    elif classification == "HAM" and confidence < 0.55:
        score += 10.0
        factors.append(f"Low model confidence ({confidence * 100:.0f}%) in the HAM result")

    # RAG evidence pointing at high-risk families
    for hit in rag_evidence:
        category = str(hit.get("category", ""))
        if category in HIGH_RISK_CATEGORIES:
            score += settings.RISK_RAG_CATEGORY_BONUS
            factors.append(f"Retrieved knowledge matches the {category} family")
            break

    score = _clamp(score)

    # floor: any SPAM classification is at least MEDIUM risk
    level = _level(score)
    if classification == "SPAM" and level == "LOW":
        level = "MEDIUM"

    return {"score": round(score, 1), "level": level, "factors": factors}