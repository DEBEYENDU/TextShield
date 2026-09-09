"""Structured message profile — the single understanding artifact.

Example:
    Category: Educational Announcement | Intent: Congratulate
    Threat Score: 0.08 | Trust Score: 0.91 | Entities: 6 | URLs: 0
    Credential Requests: 0 | Urgency: No | Payment Request: No
    Overall Context: Institutional communication.
"""

from __future__ import annotations

_RISK_BANDS = [(0.15, "Very Low"), (0.35, "Low"), (0.6, "Medium"), (0.8, "High"), (2.0, "Critical")]


def _risk_band(threat_score: float) -> str:
    for ceiling, label in _RISK_BANDS:
        if threat_score < ceiling:
            return label
    return "Critical"


class MessageProfile:
    """Build the profile dict from stage outputs."""

    def build(self, language: dict, msg_type: dict, intent: dict,
              entities: dict, evidence: dict, elapsed_ms: float) -> dict:
        urls = entities.get("urls", [])
        threat_families = {i.get("family", "") for i in
                           [x for x in evidence.get("threat_indicators", [])]}
        credential_requests = sum(
            1 for i in evidence.get("threat_indicators", [])
            if "credential" in str(i.get("indicator", "")).lower())
        urgency = any("urgency" in str(i.get("indicator", "")).lower()
                      for i in evidence.get("threat_indicators", []))
        payment = any(k in str(i.get("indicator", "")).lower()
                      for k in ("payment", "money_transfer", "fee")
                      for i in evidence.get("threat_indicators", []))
        threat_score = float(evidence.get("threat_score", 0.0))
        trust_score = float(evidence.get("trust_score", 0.0))
        context = self._overall_context(msg_type.get("type", "Unknown"),
                                        intent.get("intent", "Inform"),
                                        threat_score, trust_score)
        return {
            "category": msg_type.get("type", "Unknown"),
            "category_confidence": msg_type.get("confidence", 0.0),
            "category_evidence": msg_type.get("evidence", []),
            "intent": intent.get("intent", "Inform"),
            "intent_confidence": intent.get("confidence", 0.0),
            "intent_reasoning": intent.get("reasoning", ""),
            "language": language.get("language", "unknown"),
            "language_confidence": language.get("confidence", 0.0),
            "threat_score": threat_score,
            "trust_score": trust_score,
            "risk": _risk_band(threat_score),
            "entities": entities.get("total_count", 0),
            "entity_detail": {k: v for k, v in entities.items() if k != "total_count"},
            "urls": len(urls),
            "credential_requests": credential_requests,
            "urgency": "Yes" if urgency else "No",
            "payment_request": "Yes" if payment else "No",
            "overall_context": context,
            "threat_families": sorted(f for f in threat_families if f),
            "understanding_latency_ms": round(elapsed_ms, 2),
        }

    @staticmethod
    def _overall_context(category: str, intent: str, threat: float, trust: float) -> str:
        if threat >= 0.6:
            return f"High-risk {category.lower()} pattern requesting {intent.lower()}."
        if trust >= 0.6 and threat < 0.3:
            return "Institutional communication."
        if category in {"OTP / Authentication", "Bank Notification", "Payment Confirmation"} \
                and threat < 0.4:
            return "Routine transactional notification."
        if threat >= 0.35:
            return f"Suspicious {category.lower()} message; verify through official channels."
        return f"Everyday {category.lower()} communication."


message_profile = MessageProfile()
