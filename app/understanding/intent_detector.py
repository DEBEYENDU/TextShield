"""Intent detection over the RFC-001 taxonomy (16 intents).

Combines the legacy request-intent engine (app.ml.intent) with a semantic
phrase-scoring layer for communicative intents (inform, congratulate,
recruit, ...). Returns {intent, confidence, reasoning}.
"""

from __future__ import annotations

import re

from app.ml import intent as legacy_intent

# Intent -> [(phrase, weight)]. Communicative + transactional coverage.
_INTENT_PHRASES: dict[str, list[tuple[str, float]]] = {
    "Congratulate": [
        ("congratulations", 1.6), ("well done", 1.4), ("proud of you", 1.5),
        ("best wishes", 1.2), ("you have been selected", 1.3),
        ("pleased to announce", 1.3), ("kudos", 1.2),
    ],
    "Recruit": [
        ("we are hiring", 1.7), ("apply", 0.8), ("walk-in interview", 1.6),
        ("shortlisted", 1.4), ("job offer", 1.3), ("join our team", 1.5),
        ("send your resume", 1.4), ("open positions", 1.3),
    ],
    "Authenticate": [
        ("one time password", 1.7), ("otp", 1.2), ("verification code", 1.5),
        ("login attempt", 1.3), ("use this code to", 1.4), ("2fa", 1.3),
        ("two-factor", 1.3),
    ],
    "Verify Identity": [
        ("verify your identity", 1.7), ("confirm your identity", 1.6),
        ("kyc verification", 1.4), ("upload.*id proof", 1.4),
        ("identity proof", 1.3), ("complete.*verification", 1.2),
    ],
    "Collect Information": [
        ("share your.*details", 1.5), ("provide.*information", 1.3),
        ("fill.*form", 1.3), ("submit.*documents", 1.3),
        ("update.*details", 1.1), ("enter.*password", 1.4),
    ],
    "Request Action": [
        ("please.*reply", 1.2), ("click.*link", 1.3), ("download.*app", 1.3),
        ("pay.*fee", 1.4), ("transfer.*amount", 1.4), ("act now", 1.2),
        ("confirm.*account", 1.3),
    ],
    "Warn": [
        ("beware of", 1.5), ("fraud alert", 1.5), ("stay safe", 1.2),
        ("do not share", 1.3), ("warning", 1.0), ("protect yourself", 1.3),
        ("advisory", 1.0),
    ],
    "Promote": [
        ("limited.*offer", 1.5), ("flat.*off", 1.5), ("mega sale", 1.4),
        ("exclusive deal", 1.3), ("festive offer", 1.3), ("use code", 1.1),
    ],
    "Advertise": [
        ("introducing", 1.2), ("brand new", 1.2), ("launch", 0.8),
        ("check out our", 1.3), ("now available", 1.1), ("sponsored", 1.3),
    ],
    "Sell": [
        ("buy now", 1.5), ("order now", 1.4), ("add to cart", 1.5),
        ("cash on delivery", 1.2), ("checkout", 1.0), ("place your order", 1.4),
    ],
    "Notify": [
        ("this is to inform", 1.5), ("please note", 1.2), ("be advised", 1.3),
        ("notification", 1.0), ("status update", 1.2), ("scheduled maintenance", 1.4),
    ],
    "Inform": [
        ("here are the details", 1.3), ("for your information", 1.4),
        ("announcement", 1.1), ("circular", 1.2), ("please find attached", 1.3),
        ("results declared", 1.3),
    ],
    "Reminder": [
        ("reminder", 1.5), ("due tomorrow", 1.4), ("last date", 1.3),
        ("don't forget", 1.3), ("gentle reminder", 1.6), ("upcoming", 0.8),
    ],
    "Update": [
        ("has been updated", 1.4), ("new version", 1.2), ("shipped", 1.1),
        ("out for delivery", 1.3), ("delivered", 1.0), ("rescheduled", 1.2),
        ("revised", 1.1),
    ],
    "Support": [
        ("how can we help", 1.5), ("ticket.*raised", 1.4), ("support team", 1.2),
        ("we are looking into", 1.3), ("apologize for the inconvenience", 1.3),
        ("contact us", 0.9),
    ],
    "Survey": [
        ("take.*survey", 1.6), ("feedback form", 1.5), ("rate your experience", 1.5),
        ("2-minute survey", 1.5), ("your opinion", 1.2),
    ],
}

_COMPILED = {k: [(re.compile(p, re.IGNORECASE), w) for p, w in v]
             for k, v in _INTENT_PHRASES.items()}

# Legacy request labels mapped onto the RFC taxonomy.
_LEGACY_MAP = {
    "credential_request": "Verify Identity",
    "money_transfer": "Request Action",
    "download_install": "Request Action",
    "personal_data": "Collect Information",
    "prize_claim": "Promote",
    "confirmation_request": "Verify Identity",
    "engagement": "Inform",
    "other": None,
}


class IntentDetector:
    """Score all 16 intents; legacy engine contributes request-side evidence."""

    def detect(self, text: str) -> dict:
        lowered = text or ""
        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = {}
        for intent, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                found = pattern.findall(lowered)
                if found:
                    total += weight * (1.0 + 0.2 * (len(found) - 1))
                    snippet = found[0] if isinstance(found[0], str) else found[0][0]
                    hits.append(snippet[:40])
            if total > 0:
                scores[intent] = total
                reasons[intent] = hits[:3]
        # legacy engine vote (request-oriented intents)
        try:
            legacy = legacy_intent.detect_intent(lowered)
            mapped = _LEGACY_MAP.get(legacy.get("label", "other"))
            if mapped and legacy.get("evidence"):
                scores[mapped] = scores.get(mapped, 0.0) + 1.0
                reasons.setdefault(mapped, []).append(f"request pattern: {legacy['evidence'][:40]}")
        except Exception:
            pass
        if not scores or max(scores.values()) < 0.8:
            return {"intent": "Inform", "confidence": 0.35,
                    "reasoning": "no dominant intent signals; defaulted to Inform"}
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best, best_score = ranked[0]
        runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = (best_score - runner_up) / max(best_score, 1e-9)
        confidence = round(min(0.95, 0.45 + 0.5 * margin), 3)
        return {"intent": best, "confidence": confidence,
                "reasoning": f"matched {len(reasons[best])} signal(s): " + "; ".join(reasons[best])}


intent_detector = IntentDetector()
