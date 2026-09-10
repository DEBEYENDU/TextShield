"""Manipulation verdict composer: fuses psychology, persuasion, authority
and urgency signals into an overall manipulation assessment.

The composer weights and narrates — it never classifies the message.
"""

from __future__ import annotations

_HIGH_RISK_TECHNIQUES = {"Fear", "Pressure", "Authority Bias", "Urgency"}
_HIGH_RISK_PERSUASION = {"Threat", "Fear Appeal", "Identity Verification",
                         "Financial Pressure"}
_HIGH_RISK_PERSONAS = {"CEO Fraud", "Tech Support", "Police", "Bank Representative",
                       "Government Official", "Income Tax"}


class ManipulationAnalyzer:
    """Combine sub-engine outputs into a manipulation score 0..1 + narrative."""

    def analyze(self, psychology: dict, persuasion: dict,
                authority: dict, urgency: dict) -> dict:
        techniques: list[str] = list(psychology.get("names", []))
        techniques += [p for p in persuasion.get("names", []) if p not in techniques]
        personas = authority.get("names", [])
        score = 0.0
        for item in psychology.get("techniques", []):
            w = 1.4 if item["technique"] in _HIGH_RISK_TECHNIQUES else 0.8
            score += item["score"] * w * 0.25
        for item in persuasion.get("techniques", []):
            w = 1.4 if item["technique"] in _HIGH_RISK_PERSUASION else 0.8
            score += item["score"] * w * 0.25
        for item in authority.get("personas", []):
            w = 1.5 if item["persona"] in _HIGH_RISK_PERSONAS else 0.7
            score += item["score"] * w * 0.25
        score += urgency.get("urgency_score", 0.0) * 1.2
        manipulation_score = round(min(1.0, score / 3.0), 3)
        if manipulation_score >= 0.6:
            level, narrative = "High", ("Strong multi-channel manipulation: "
                                        "combines influence techniques with pressure.")
        elif manipulation_score >= 0.35:
            level, narrative = "Medium", ("Notable persuasion signals present; "
                                          "verify requests through official channels.")
        elif manipulation_score >= 0.15:
            level, narrative = "Low", "Mild persuasive language; no coercion pattern."
        else:
            level, narrative = "Minimal", "No meaningful manipulation pattern detected."
        return {"manipulation_score": manipulation_score, "level": level,
                "techniques": techniques, "personas": personas,
                "narrative": narrative, "count": len(techniques)}
