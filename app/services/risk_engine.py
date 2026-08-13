"""Risk engine (V2.0).

Risk is scored on a 0-100 scale and mapped to one of five levels:

    LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN

Inputs (all transparent and logged as ``risk_factors``):

* ML classification + confidence
* detected indicators (severity-weighted)
* sender intent (credential/money/download requests raise the ceiling)
* URL pattern warnings
* RAG evidence pointing at high-risk knowledge categories

Rules (per PRD section 20):

* CRITICAL requires a malicious-intent signal *and* strong corroboration
  (high-confidence SPAM verdict plus high-severity indicators or risky
  URLs) - it is never granted on weak evidence.
* UNCERTAIN is reserved for irreconcilable evidence: the model is
  guessing (confidence below the uncertain threshold) and no strong
  corroborating signal exists either way. It never masquerades as a
  confident verdict.

Weights are defined in ``app/core/config.py`` so the logic is
configurable. Informational only - not legal, financial or security
authority.
"""
from __future__ import annotations

from app.core.config import settings
from app.ml.intent import is_malicious_intent


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
    intent: dict | None = None,
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

    # sender intent (engineered requests raise the risk ceiling)
    intent_label = (intent or {}).get("label", "other")
    intent_malicious = is_malicious_intent(intent_label)
    if intent_malicious:
        score += settings.RISK_INTENT_MALICIOUS
        factors.append(f"Sender intent is a {intent_label} request")

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

    # CRITICAL: malicious intent + strong corroboration (RZ-03). A high raw
    # score alone can never reach CRITICAL - the intent signal is mandatory.
    critical_intents = {"credential_request", "money_transfer", "download_install"}
    has_high_indicator = any(
        i.get("severity") == "high" for i in indicators
    )
    has_flagged_url = any(u.get("warnings") for u in urls)
    if (
        classification == "SPAM"
        and intent_label in critical_intents
        and confidence >= settings.RISK_CRITICAL_CONFIDENCE
        and score >= settings.RISK_CRITICAL_THRESHOLD
        and (has_high_indicator or has_flagged_url)
    ):
        level = "CRITICAL"
        factors.append(
            "CRITICAL: credential/money/download intent with high-confidence SPAM "
            "verdict and corroborating high-severity signals"
        )

    # UNCERTAIN: model is guessing and no evidence points either way (RZ-04)
    if (
        confidence < settings.RISK_UNCERTAIN_CONFIDENCE
        and level == "LOW"
        and not intent_malicious
        and not indicators
        and not has_flagged_url
    ):
        level = "UNCERTAIN"
        factors.append(
            "UNCERTAIN: model confidence is too low to trust and no strong "
            "corroborating indicator exists in either direction"
        )

    return {"score": round(score, 1), "level": level, "factors": factors}