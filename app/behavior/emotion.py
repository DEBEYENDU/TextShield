"""Emotion-influence estimation — persuasion focus, not sentiment analysis.

Scores 12 emotions by manipulative language (fear appeals, hype, false
hope, manufactured confusion/pressure) rather than generic positive /
negative sentiment. Returns a normalized emotion_profile {emotion: 0..1}.
"""

from __future__ import annotations

import re

# emotion -> [(phrase, weight)]
_EMOTION_PHRASES: dict[str, list[tuple[str, float]]] = {
    "Fear": [("account.*(blocked|suspended)", 1.4), ("legal action", 1.3),
             ("arrest", 1.4), ("fraud detected", 1.2), ("money at risk", 1.3),
             ("beware", 1.0)],
    "Excitement": [("amazing offer", 1.2), ("congratulations", 1.3),
                   ("you won", 1.4), ("jackpot", 1.3), ("unbelievable", 1.1)],
    "Happiness": [("good news", 1.1), ("happy to announce", 1.2),
                  ("delighted", 1.1), ("celebration", 1.0)],
    "Curiosity": [("secret", 1.1), ("you won't believe", 1.3),
                  ("mystery", 1.1), ("reveal", 1.0), ("shocking", 1.2)],
    "Stress": [("overdue", 1.2), ("pending action", 1.2), ("immediately", 1.0),
               ("compliance required", 1.2), ("resolve.*today", 1.2)],
    "Pressure": [("final warning", 1.4), ("last chance", 1.3),
                 ("must.*now", 1.2), ("no extension", 1.3), ("act or", 1.2)],
    "Trust": [("official", 0.9), ("verified", 0.9), ("guaranteed safe", 1.1),
              ("rbi registered", 1.2), ("trusted", 1.0), ("sincerely", 0.7)],
    "Hope": [("good opportunity", 1.1), ("bright future", 1.2),
             ("financial freedom", 1.3), ("dream job", 1.2), ("new beginning", 1.0)],
    "Greed": [("double.*money", 1.4), ("earn.*daily", 1.2),
              ("guaranteed.*profit", 1.4), ("free cash", 1.3), ("bonus", 0.9)],
    "Confusion": [("conflicting.*instruction", 1.3), ("urgent.*but.*wait", 1.2),
                  ("do not.*but also", 1.2), ("complicated.*process", 1.1)],
    "Urgency": [("hurry", 1.2), ("expires", 1.1), ("today only", 1.2),
                ("at once", 1.1), ("asap", 1.0)],
    "Panic": [("immediately.*otherwise", 1.4), ("within.*hour.*blocked", 1.4),
              ("emergency.*transfer", 1.4), ("don't think.*just", 1.3)],
}

_COMPILED = {k: [(re.compile(p, re.IGNORECASE), w) for p, w in v]
             for k, v in _EMOTION_PHRASES.items()}

# emotions weaponized for persuasion weigh more in the overall picture
_PERSUASION_WEIGHT = {"Fear": 1.3, "Panic": 1.4, "Greed": 1.3, "Pressure": 1.2,
                      "Urgency": 1.1, "Stress": 1.0, "Excitement": 1.0,
                      "Curiosity": 1.0, "Hope": 0.9, "Trust": 0.8,
                      "Happiness": 0.7, "Confusion": 1.0}


class EmotionAnalyzer:
    """Estimate manipulative emotional influence per emotion."""

    def analyze(self, text: str) -> dict:
        lowered = text or ""
        raw: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}
        for emotion, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                found = pattern.findall(lowered)
                if found:
                    total += weight * (1.0 + 0.2 * (len(found) - 1))
                    snippet = found[0] if isinstance(found[0], str) else found[0][0]
                    hits.append(" ".join(str(snippet).split())[:45])
            if total > 0:
                raw[emotion] = total
                evidence[emotion] = hits[:3]
        peak = max(raw.values()) if raw else 0.0
        profile = {e: round(min(1.0, v / max(peak, 1.0)), 3) for e, v in raw.items()}
        dominant = max(raw, key=raw.get) if raw else "Neutral"
        weaponized = round(sum(raw.get(e, 0.0) * _PERSUASION_WEIGHT.get(e, 1.0)
                               for e in raw) / 4.0, 3)
        return {"emotion_profile": profile, "dominant": dominant,
                "evidence": evidence, "weaponized_score": min(1.0, weaponized),
                "count": len(raw)}
