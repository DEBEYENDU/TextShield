"""Persuasion technique analysis: reward promises, threats, authority
references, exclusive offers, fear appeals, financial/emotional pressure,
identity verification demands and false reassurance.

Returns {technique, confidence, evidence} per detected technique.
"""

from __future__ import annotations

import re

# technique -> [(phrase, weight)]
_PERSUASION_PHRASES: dict[str, list[tuple[str, float]]] = {
    "Reward Promise": [
        ("claim.*(prize|reward|bonus|cashback)", 1.5), ("you have won", 1.4),
        ("guaranteed.*(returns|profit|income)", 1.5), ("free.*(gift|iphone|recharge)", 1.3),
        ("cashback.*credited", 1.2),
    ],
    "Threat": [
        ("account.*(blocked|suspended|closed)", 1.5), ("legal action.*taken", 1.4),
        ("fir.*filed", 1.4), ("service.*terminated", 1.3),
        ("pay.*or.*face", 1.3),
    ],
    "Authority Reference": [
        ("rbi", 1.0), ("reserve bank", 1.2), ("income tax", 1.1),
        ("supreme court", 1.3), ("ministry of", 1.1), ("ceo", 1.0),
        ("government.*order", 1.2),
    ],
    "Exclusive Offer": [
        ("exclusively for you", 1.4), ("only for (selected|chosen)", 1.4),
        ("vip.*access", 1.2), ("private sale", 1.2), ("members? only", 1.1),
    ],
    "Fear Appeal": [
        ("your.*at risk", 1.3), ("fraud.*detected", 1.3),
        ("someone.*accessing", 1.2), ("breach.*account", 1.2),
        ("protect.*immediately", 1.1),
    ],
    "Financial Pressure": [
        ("pay.*(fee|now|today|immediately)", 1.4), ("transfer.*amount", 1.3),
        ("transfer.*(today|new account)", 1.3),
        ("advance.*payment", 1.3), ("processing.*charges", 1.2),
        ("refundable.*deposit", 1.2),
    ],
    "Emotional Pressure": [
        ("don't disappoint", 1.3), ("after everything", 1.2),
        ("we trusted you", 1.3), ("please.*beg", 1.2), ("for my *sake", 1.2),
    ],
    "Identity Verification": [
        ("verify.*(identity|account|kyc)", 1.4), ("upload.*(id|document|proof)", 1.3),
        ("share.*(otp|password|pin)", 1.5), ("confirm.*credentials", 1.4),
        ("kyc.*(update|pending|verify)", 1.3),
    ],
    "False Reassurance": [
        ("100% (safe|secure|genuine)", 1.5), ("no risk", 1.3),
        ("fully (protected|encrypted)", 1.2), ("don't worry", 1.1),
        ("completely legitimate", 1.4), ("trust.*blindly", 1.3),
    ],
}

_COMPILED = {k: [(re.compile(p, re.IGNORECASE), w) for p, w in v]
             for k, v in _PERSUASION_PHRASES.items()}


class PersuasionAnalyzer:
    """Detect persuasion techniques with confidence and evidence."""

    def analyze(self, text: str) -> dict:
        lowered = text or ""
        found: list[dict] = []
        for technique, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                matches = pattern.findall(lowered)
                if matches:
                    total += weight * (1.0 + 0.2 * (len(matches) - 1))
                    snippet = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    hits.append(" ".join(str(snippet).split())[:50])
            if total >= 1.0:
                found.append({"technique": technique,
                              "confidence": round(min(0.95, 0.40 + 0.18 * total), 3),
                              "evidence": hits[:3], "score": round(total, 2)})
        found.sort(key=lambda t: -t["score"])
        return {"techniques": found,
                "names": [t["technique"] for t in found],
                "count": len(found)}
