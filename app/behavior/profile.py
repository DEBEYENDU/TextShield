"""Communication style classifier (13 styles) and behavior profile builder.

Style scoring fuses linguistic metrics, conversation structure, message
type context and manipulation level — no single signal decides.
"""

from __future__ import annotations

_STYLE_SIGNALS: dict[str, list[tuple[str, float]]] = {
    # (signal description, weight) — evaluated against the evidence bundle
    "Formal": [("greeting+closing", 1.2), ("professional tone", 1.1),
               ("good grammar", 0.8)],
    "Professional": [("professional tone", 1.4), ("consistent formatting", 1.0),
                     ("moderate complexity", 0.7)],
    "Corporate": [("corporate type", 1.5), ("professional tone", 1.0),
                  ("informational flow", 0.8)],
    "Academic": [("educational type", 1.5), ("formal greeting", 0.9),
                 ("complex sentences", 0.7)],
    "Government": [("government type", 1.5), ("formal", 1.0), ("reference numbers", 0.8)],
    "Marketing": [("promotional type", 1.4), ("excitement emotion", 0.9),
                  ("exclusive offer", 1.0)],
    "Conversational": [("questions present", 1.0), ("casual tone", 1.2),
                       ("personal type", 1.0)],
    "Transactional": [("transactional type", 1.5), ("official terminology", 0.9),
                      ("neutral tone", 0.7)],
    "Informal": [("casual tone", 1.3), ("slang/emoji", 1.0), ("simple sentences", 0.6)],
    "Aggressive": [("aggressive tone", 1.6), ("caps/punct abuse", 1.2),
                   ("abrupt demand", 1.1)],
    "Manipulative": [("high manipulation", 1.7), ("pressure flow high", 1.2),
                     ("false reassurance", 1.0)],
    "Emotional": [("weaponized emotion", 1.3), ("sympathy/guilt", 1.1),
                  ("emotional pressure", 1.0)],
    "Neutral": [("no strong signals", 0.6)],
}


class StyleClassifier:
    """Score styles from the cross-engine evidence bundle."""

    def classify(self, bundle: dict) -> dict:
        ling = bundle.get("linguistic", {})
        conv = bundle.get("conversation", {})
        manip = bundle.get("manipulation", {})
        emotion = bundle.get("emotion", {})
        msg_type = str(bundle.get("message_type", "Unknown"))
        scores: dict[str, float] = {}
        evidence: dict[str, list[str]] = {}

        def add(style: str, weight: float, why: str):
            scores[style] = scores.get(style, 0.0) + weight
            evidence.setdefault(style, []).append(why)

        tone = ling.get("professional_tone", "Neutral")
        if tone == "Professional":
            add("Professional", 1.4, "professional tone")
            add("Formal", 1.1, "professional tone")
        if tone == "Casual":
            add("Conversational", 1.2, "casual tone")
            add("Informal", 1.3, "casual tone")
        if tone == "Aggressive":
            add("Aggressive", 1.6, "aggressive tone")
        if ling.get("formatting") == "Consistent":
            add("Formal", 1.2, "greeting+closing")
            add("Professional", 1.0, "consistent formatting")
        if ling.get("grammar_quality") == "Good":
            add("Formal", 0.8, "good grammar")
        if ling.get("sentence_complexity") in {"Complex", "Very Complex"}:
            add("Academic", 0.7, "complex sentences")
        if ling.get("sentence_complexity") == "Simple":
            add("Informal", 0.6, "simple sentences")
        if ling.get("abuse_signals"):
            add("Aggressive", 1.2, "caps/punct abuse")
        if conv.get("flow") == "Informational":
            add("Corporate", 0.8, "informational flow")
        if conv.get("flow") == "Abrupt Demand":
            add("Aggressive", 1.1, "abrupt demand")
        if conv.get("pressure_flow") == "High":
            add("Manipulative", 1.2, "pressure flow high")
        if conv.get("question_count", 0) >= 2:
            add("Conversational", 1.0, "questions present")
        if manip.get("level") == "High":
            add("Manipulative", 1.7, "high manipulation")
        if emotion.get("weaponized_score", 0) >= 0.5:
            add("Emotional", 1.3, "weaponized emotion")
        if "Sympathy" in emotion.get("emotion_profile", {}) or \
                "Guilt" in str(manip.get("techniques", [])):
            add("Emotional", 1.1, "sympathy/guilt")
        if "False Reassurance" in str(bundle.get("persuasion", {}).get("names", [])):
            add("Manipulative", 1.0, "false reassurance")
        type_map = {"Recruitment": "Corporate", "Bank Notification": "Transactional",
                    "Government Advisory": "Government",
                    "Educational Announcement": "Academic",
                    "Promotional Advertisement": "Marketing",
                    "Personal Communication": "Conversational",
                    "OTP / Authentication": "Transactional",
                    "Payment Confirmation": "Transactional",
                    "Healthcare": "Formal", "Courier / Logistics": "Transactional",
                    "Telecom": "Transactional", "Travel": "Transactional",
                    "Invoice": "Transactional", "Meeting Invitation": "Corporate",
                    "Technical Support": "Professional",
                    "Subscription": "Transactional",
                    "E-commerce": "Transactional",
                    "Investment": "Transactional",
                    "Newsletter": "Neutral",
                    "Social Media": "Conversational"}
        if msg_type in type_map:
            add(type_map[msg_type], 1.5, f"{msg_type.lower()} type")
        if not scores:
            return {"style": "Neutral", "confidence": 0.35, "evidence": ["no strong signals"]}
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        best, best_score = ranked[0]
        runner = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = (best_score - runner) / max(best_score, 1e-9)
        return {"style": best,
                "confidence": round(min(0.95, 0.45 + 0.5 * margin), 3),
                "evidence": evidence.get(best, [])[:4]}


class BehaviorProfileBuilder:
    """Assemble the RFC-004 behavior profile dict."""

    def build(self, bundle: dict, elapsed_ms: float) -> dict:
        psychology = bundle.get("psychology", {})
        authority = bundle.get("authority", {})
        emotion = bundle.get("emotion", {})
        urgency = bundle.get("urgency", {})
        persuasion = bundle.get("persuasion", {})
        manip = bundle.get("manipulation", {})
        style = bundle.get("style", {})
        triggers = sorted({t["technique"] for t in psychology.get("techniques", [])} |
                          {t["technique"] for t in persuasion.get("techniques", [])})
        return {
            "communication_style": style.get("style", "Neutral"),
            "style_confidence": style.get("confidence", 0.0),
            "psychological_triggers": triggers,
            "social_engineering": authority.get("names", []),
            "emotion_profile": emotion.get("emotion_profile", {}),
            "dominant_emotion": emotion.get("dominant", "Neutral"),
            "urgency": {"score": urgency.get("urgency_score", 0.0),
                        "level": urgency.get("level", "Low"),
                        "evidence": urgency.get("evidence", [])},
            "persuasion": persuasion.get("names", []),
            "manipulation_score": manip.get("manipulation_score", 0.0),
            "manipulation_level": manip.get("level", "Minimal"),
            "overall_behavior": self._overall(manip.get("level", "Minimal"),
                                             style.get("style", "Neutral"),
                                             urgency.get("level", "Low")),
            "confidence": round(float(style.get("confidence", 0.0)), 3),
            "analysis_latency_ms": round(elapsed_ms, 2),
        }

    @staticmethod
    def _overall(manip_level: str, style: str, urgency_level: str) -> str:
        if manip_level == "High":
            return f"Coercive {style.lower()} communication with heavy pressure tactics."
        if manip_level == "Medium":
            return f"Persuasive {style.lower()} message; verify any requested actions."
        if style in {"Formal", "Professional", "Corporate", "Academic",
                     "Government", "Transactional"}:
            return f"Routine {style.lower()} communication."
        if urgency_level in {"Critical", "High"}:
            return "Time-pressured message; treat requests with caution."
        return f"Everyday {style.lower()} communication."
