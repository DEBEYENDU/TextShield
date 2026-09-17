"""Psychological manipulation technique detection (18 techniques).

Multi-signal scoring: weighted semantic phrases plus structural boosts
(imperatives, questions, money/URL presence). Returns techniques with
confidence and quoted evidence — never a verdict.
"""

from __future__ import annotations

import re

# technique -> [(phrase, weight)]
_TECHNIQUE_PHRASES: dict[str, list[tuple[str, float]]] = {
    "Authority Bias": [
        ("as per rbi guidelines", 1.6), ("reserve bank of india", 1.2),
        ("by order of", 1.4), ("government mandated", 1.4),
        ("official directive", 1.4), ("from the desk of", 1.2),
        ("authorized by", 1.1), ("ceo office", 1.2), ("head office", 1.0),
        ("ministry has directed", 1.4),
    ],
    "Urgency": [
        ("act now", 1.5), ("immediately", 1.1), ("urgent", 1.2),
        ("within \\d+ hours?", 1.4), ("right away", 1.2), ("asap", 1.1),
        ("at once", 1.1), ("without delay", 1.3),
    ],
    "Fear": [
        ("account will be blocked", 1.6), ("account (blocked|suspended|frozen)", 1.4),
        ("legal action", 1.4), ("arrest warrant", 1.5), ("fraud detected", 1.3),
        ("unauthorized access", 1.2), ("your money is at risk", 1.4),
        ("account compromised", 1.4), ("penalty will be imposed", 1.3),
        ("virus detected", 1.3), ("device.*infected", 1.3),
        ("security alert", 1.2), ("data.*(breach|leak)", 1.2),
    ],
    "Scarcity": [
        ("only \\d+ (left|slots|seats|remaining)", 1.6), ("limited stock", 1.4),
        ("offer ends", 1.3), ("last day", 1.2), ("final call", 1.2),
        ("first \\d+ (callers|users|customers)", 1.4), ("while stocks last", 1.3),
    ],
    "Greed": [
        ("double your money", 1.6), ("guaranteed returns", 1.5),
        ("earn .* per day", 1.3), ("risk-free profit", 1.5),
        ("get rich", 1.4), ("passive income", 1.2), ("daily profit", 1.3),
    ],
    "Curiosity": [
        ("you won't believe", 1.4), ("secret (method|trick|offer)", 1.3),
        ("shocking truth", 1.4), ("see what happened", 1.2),
        ("open to reveal", 1.3), ("mystery (gift|prize|box)", 1.3),
    ],
    "Reciprocity": [
        ("free gift for you", 1.4), ("as a thank you", 1.3),
        ("exclusive bonus", 1.2), ("on the house", 1.3),
        ("we've credited.*bonus", 1.3), ("complimentary", 1.1),
    ],
    "Commitment": [
        ("you agreed to", 1.3), ("as promised", 1.2), ("confirm your commitment", 1.4),
        ("complete your registration", 1.2), ("finish what you started", 1.3),
    ],
    "Social Proof": [
        ("\\d+[,\\d]* (people|users|customers) (have )?(joined|earned|won)", 1.5),
        ("everyone is", 1.1), ("your friends are", 1.2), ("trending now", 1.1),
        ("rated .* stars", 1.0), ("testimonials", 1.2), ("success stories", 1.2),
    ],
    "Loss Aversion": [
        ("don't miss out", 1.4), ("you will lose", 1.4), ("miss this chance", 1.3),
        ("avoid losing", 1.3), ("protect your money", 1.1),
        ("last chance to save", 1.4),
    ],
    "Reward Seeking": [
        ("claim your (prize|reward|cashback|bonus)", 1.6), ("you have won", 1.5),
        ("congratulations.*winner", 1.4), ("cashback of", 1.2),
        ("reward points", 1.1), ("collect your", 1.1),
    ],
    "FOMO": [
        ("ending soon", 1.3), ("almost gone", 1.3), ("selling fast", 1.2),
        ("before it's too late", 1.4), ("expires? tonight", 1.3),
        ("today only", 1.2),
    ],
    "Sympathy": [
        ("please help", 1.3), ("i am in trouble", 1.5), ("stranded", 1.3),
        ("medical emergency", 1.3), ("god bless", 1.0), ("kindly help", 1.2),
    ],
    "Empathy Exploitation": [
        ("i know how you feel", 1.3), ("as a fellow", 1.2),
        ("we understand your pain", 1.4), ("you deserve", 1.1),
        ("trust me", 1.2),
    ],
    "Trust Building": [
        ("100% (safe|secure|genuine|verified)", 1.4), ("government approved", 1.3),
        ("rbi registered", 1.4), ("iso certified", 1.2), ("trusted by lakhs", 1.3),
        ("no risk involved", 1.3), ("fully secure", 1.1),
    ],
    "Guilt": [
        ("after all we've done", 1.4), ("you owe", 1.2), ("ungrateful", 1.3),
        ("we trusted you", 1.3), ("don't let us down", 1.3),
    ],
    "Pressure": [
        ("final warning", 1.5), ("last notice", 1.4), ("act or face", 1.4),
        ("no further reminders", 1.3), ("immediate compliance", 1.3),
        ("respond within", 1.2),
    ],
    "Time Constraints": [
        ("deadline", 1.2), ("due by", 1.1), ("valid till", 1.1),
        ("offer valid", 1.1), ("last date", 1.2), ("expires? on", 1.1),
        ("within 24 hours", 1.4),
    ],
}

_COMPILED = {k: [(re.compile(p, re.IGNORECASE), w) for p, w in v]
             for k, v in _TECHNIQUE_PHRASES.items()}

_IMPERATIVE = re.compile(
    r"^(please |kindly |do not |don't |never |always |click |tap |send |share |"
    r"pay |transfer |verify |confirm |call |download |install |open |enter |submit )",
    re.IGNORECASE | re.MULTILINE)


class PsychologyDetector:
    """Score all 18 techniques; structural signals boost, never decide."""

    def detect(self, text: str) -> dict:
        lowered = text or ""
        techniques: list[dict] = []
        sentences = [s for s in re.split(r"[.!?\n]+", lowered) if s.strip()]
        imperatives = sum(1 for s in sentences if _IMPERATIVE.search(s.strip()))
        imperative_boost = min(0.3, 0.1 * imperatives)
        for technique, patterns in _COMPILED.items():
            total = 0.0
            hits: list[str] = []
            for pattern, weight in patterns:
                found = pattern.findall(lowered)
                if found:
                    total += weight * (1.0 + 0.2 * (len(found) - 1))
                    snippet = found[0] if isinstance(found[0], str) else found[0][0]
                    hits.append(" ".join(str(snippet).split())[:50])
            if total > 0:
                total += imperative_boost if technique in {
                    "Urgency", "Pressure", "Fear", "Time Constraints"} else 0.0
                confidence = round(min(0.95, 0.40 + 0.18 * total), 3)
                techniques.append({"technique": technique, "confidence": confidence,
                                   "evidence": hits[:3], "score": round(total, 2)})
        techniques.sort(key=lambda t: -t["score"])
        return {"techniques": techniques,
                "names": [t["technique"] for t in techniques],
                "count": len(techniques)}
