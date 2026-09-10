"""Semantic urgency detection — beyond bare keywords.

Combines explicit time constraints, consequence threats (suspension,
closure, penalties), final-warning language and structural pressure
signals (repeated exclamations, ALL-CAPS urgency lines) into an
urgency_score in 0..1 with supporting evidence and confidence.
"""

from __future__ import annotations

import re

_TIME_LIMIT = re.compile(
    r"\b(within \d+ (minutes?|hours?|days?)|in the next \d+ (minutes?|hours?)|"
    r"by (today|tonight|midnight|eod)|before \d+ (am|pm)|valid (for|till|until)|"
    r"expires? (today|tonight|soon|in)|today only|last date)\b", re.IGNORECASE)
_CONSEQUENCE = re.compile(
    r"\b(will be (blocked|suspended|closed|frozen|deactivated|cancelled|deleted)|"
    r"account closure|suspension|termination|legal action|penalty|"
    r"otherwise.*(blocked|charged|lost)|fail(ing|ure) to .* (result|lead))\b",
    re.IGNORECASE)
_FINAL_WARNING = re.compile(
    r"\b(final (warning|notice|reminder|call)|last (chance|warning|notice|reminder)|"
    r"no further (reminders?|extensions?|notices?)|immediate (action|attention))\b",
    re.IGNORECASE)
_EMERGENCY = re.compile(
    r"\b(emergency|critical|alert|asap|act now|hurry|at once|straight away)\b",
    re.IGNORECASE)


class UrgencyDetector:
    """Score urgency semantically; structural abuse amplifies, never decides."""

    def detect(self, text: str) -> dict:
        lowered = text or ""
        evidence: list[str] = []
        score = 0.0

        def collect(pattern: re.Pattern, weight: float, label: str):
            nonlocal score
            found = pattern.findall(lowered)
            if found:
                flat = found[0] if isinstance(found[0], str) else found[0][0]
                evidence.append(f"{label}: {' '.join(str(flat).split())[:45]}")
                score += weight * (1.0 + 0.25 * (len(found) - 1))

        collect(_TIME_LIMIT, 1.2, "time limit")
        collect(_CONSEQUENCE, 1.4, "consequence")
        collect(_FINAL_WARNING, 1.3, "final warning")
        collect(_EMERGENCY, 0.8, "emergency language")
        # structural: exclamation / caps pressure lines
        exclamations = lowered.count("!")
        if exclamations >= 3:
            evidence.append(f"repeated exclamations ({exclamations})")
            score += 0.5
        lines = [line for line in (text or "").splitlines() if line.strip()]
        caps_lines = sum(1 for line in lines
                         if len(line) > 12 and sum(c.isupper() for c in line)
                         / max(len([c for c in line if c.isalpha()]), 1) > 0.7)
        if caps_lines:
            evidence.append(f"ALL-CAPS pressure lines ({caps_lines})")
            score += 0.4 * caps_lines
        urgency_score = round(min(1.0, score / 3.0), 3)
        confidence = round(min(0.95, 0.35 + 0.2 * score), 3) if score else 0.0
        return {"urgency_score": urgency_score, "evidence": evidence[:6],
                "confidence": confidence, "level": self._level(urgency_score)}

    @staticmethod
    def _level(score: float) -> str:
        if score >= 0.7:
            return "Critical"
        if score >= 0.45:
            return "High"
        if score >= 0.2:
            return "Medium"
        return "Low"
