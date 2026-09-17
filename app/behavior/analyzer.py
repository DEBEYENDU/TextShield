"""Behavioral analyzer — the RFC-004 evidence-provider orchestrator.

Runs psychology, authority, urgency, emotion, persuasion, manipulation,
linguistic, conversation and style stages with per-stage degradation, then
derives trust/threat deltas, RAG terms and graph edges. Never classifies;
overhead target < 300 ms (regex/heuristic only, singleton reuse).
"""

from __future__ import annotations

import time

from app.behavior.authority import AuthorityDetector
from app.behavior.conversation import ConversationAnalyzer
from app.behavior.emotion import EmotionAnalyzer
from app.behavior.linguistic import LinguisticAnalyzer
from app.behavior.manipulation import ManipulationAnalyzer
from app.behavior.persuasion import PersuasionAnalyzer
from app.behavior.profile import BehaviorProfileBuilder, StyleClassifier
from app.behavior.psychology import PsychologyDetector
from app.behavior.urgency import UrgencyDetector
from app.core.logging import get_logger

logger = get_logger(__name__)

# RAG retrieval terms per detected technique/persona family.
_RAG_TERMS = {
    "Authority Bias": ["authority bias", "impersonation"],
    "Fear": ["fear appeal", "social engineering"],
    "Urgency": ["urgency pressure"],
    "Time Constraints": ["urgency pressure"],
    "Pressure": ["coercion tactics"],
    "Reward Seeking": ["reward scam"],
    "Greed": ["investment scam"],
    "Trust Building": ["false trust signals"],
    "False Reassurance": ["false trust signals"],
    "Identity Verification": ["credential harvesting", "KYC scam"],
    "Financial Pressure": ["advance fee fraud"],
    "CEO Fraud": ["business email compromise", "CEO fraud"],
    "Tech Support": ["tech support scam"],
    "Threat": ["extortion pattern"],
}


class BehavioralAnalyzer:
    """Run all behavioral stages; never raises, never classifies."""

    engine_version = "4.0.0"

    def __init__(self) -> None:
        self.psychology = PsychologyDetector()
        self.authority = AuthorityDetector()
        self.urgency = UrgencyDetector()
        self.emotion = EmotionAnalyzer()
        self.persuasion = PersuasionAnalyzer()
        self.manipulation = ManipulationAnalyzer()
        self.linguistic = LinguisticAnalyzer()
        self.conversation = ConversationAnalyzer()
        self.style = StyleClassifier()
        self.profile_builder = BehaviorProfileBuilder()

    def analyze(self, text: str, message_type: str = "Unknown",
                sender: str = "") -> dict:
        started = time.perf_counter()
        full = f"{text or ''}\n{sender}" if sender else (text or "")
        result: dict = {"engine_version": self.engine_version}
        bundle: dict = {"message_type": message_type}
        for key, engine, method in (
            ("psychology", self.psychology, "detect"),
            ("authority", self.authority, "detect"),
            ("urgency", self.urgency, "detect"),
            ("emotion", self.emotion, "analyze"),
            ("persuasion", self.persuasion, "analyze"),
            ("linguistic", self.linguistic, "analyze"),
            ("conversation", self.conversation, "analyze"),
        ):
            try:
                result[key] = getattr(engine, method)(full)
            except Exception as exc:
                logger.warning("behavior %s stage failed: %s", key, exc)
                result[key] = {}
            bundle[key] = result[key]
        try:
            result["manipulation"] = self.manipulation.analyze(
                bundle["psychology"], bundle["persuasion"],
                bundle["authority"], bundle["urgency"])
        except Exception as exc:
            logger.warning("behavior manipulation stage failed: %s", exc)
            result["manipulation"] = {"manipulation_score": 0.0, "level": "Minimal"}
        bundle["manipulation"] = result["manipulation"]
        try:
            result["style"] = self.style.classify(bundle)
        except Exception as exc:
            logger.warning("behavior style stage failed: %s", exc)
            result["style"] = {"style": "Neutral", "confidence": 0.0, "evidence": []}
        bundle["style"] = result["style"]
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        try:
            result["behavior_profile"] = self.profile_builder.build(bundle, elapsed_ms)
        except Exception as exc:
            logger.warning("behavior profile stage failed: %s", exc)
            result["behavior_profile"] = {"communication_style": "Neutral",
                                          "overall_behavior": "Everyday neutral communication."}
        result["trust_adjustment"], result["threat_adjustment"], reasons = \
            self._deltas(result)
        result["adjustment_reasons"] = reasons
        result["rag_terms"] = self._rag_terms(result)
        result["graph_edges"] = self._graph_edges(result)
        result["latency_ms"] = round(elapsed_ms, 2)
        return result

    # ------------------------------------------------------------- derivatives
    @staticmethod
    def _deltas(result: dict) -> tuple[float, float, list[str]]:
        manip_score = float(result.get("manipulation", {}).get("manipulation_score", 0.0))
        urgency_score = float(result.get("urgency", {}).get("urgency_score", 0.0))
        personas = set(result.get("authority", {}).get("names", []))
        triggers = set(result.get("behavior_profile", {}).get("psychological_triggers", []))
        reasons: list[str] = []
        threat = 0.0
        if manip_score >= 0.6:
            threat += 0.12
            reasons.append(f"high manipulation score ({manip_score})")
        elif manip_score >= 0.35:
            threat += 0.06
            reasons.append(f"medium manipulation score ({manip_score})")
        if urgency_score >= 0.7:
            threat += 0.08
            reasons.append(f"critical urgency ({urgency_score})")
        risky_personas = personas & {"CEO Fraud", "Tech Support", "Police",
                                     "Bank Representative", "Government Official",
                                     "Income Tax"}
        if risky_personas:
            threat += 0.08
            reasons.append(f"high-risk persona: {sorted(risky_personas)[0]}")
        if {"Fear", "Pressure", "Threat", "Fear Appeal"} & triggers:
            threat += 0.05
            reasons.append("fear/pressure persuasion present")
        trust = 0.0
        if manip_score < 0.15 and urgency_score < 0.2 and not personas:
            trust += 0.06
            reasons.append("no manipulation, urgency or impersonation signals")
        return (round(max(-0.3, min(0.3, trust)), 3),
                round(max(-0.3, min(0.3, threat)), 3), reasons)

    @staticmethod
    def _rag_terms(result: dict) -> list[str]:
        terms: list[str] = []
        for name in (result.get("behavior_profile", {}).get("psychological_triggers", [])
                     + result.get("behavior_profile", {}).get("persuasion", [])
                     + result.get("behavior_profile", {}).get("social_engineering", [])):
            terms.extend(_RAG_TERMS.get(name, []))
        seen: set[str] = set()
        return [t for t in terms if t and not (t in seen or seen.add(t))][:8]

    @staticmethod
    def _graph_edges(result: dict) -> list[dict]:
        """Person—Uses→technique edges for the knowledge graph."""
        edges: list[dict] = []
        for persona in result.get("authority", {}).get("names", [])[:3]:
            for technique in (result.get("behavior_profile", {})
                              .get("psychological_triggers", [])[:4]):
                edges.append({"src_label": persona, "src_type": "PERSON",
                              "rel": "Uses", "dst_label": technique,
                              "dst_type": "ATTACK_PATTERN",
                              "evidence": f"{persona} employs {technique}"})
        for technique in (result.get("behavior_profile", {}).get("persuasion", [])[:3]):
            edges.append({"src_label": technique, "src_type": "ATTACK_PATTERN",
                          "rel": "TARGETS", "dst_label": "Message Recipient",
                          "dst_type": "PERSON",
                          "evidence": f"persuasion via {technique}"})
        return edges[:10]


behavioral_analyzer = BehavioralAnalyzer()

__all__ = ["BehavioralAnalyzer", "behavioral_analyzer", "behavior_context_block"]


def behavior_context_block(result: dict) -> str:
    """Render the behavior profile as an LLM prompt section."""
    profile = result.get("behavior_profile", {})
    lines = ["BEHAVIORAL ANALYSIS (influence evidence — context, not verdict):"]
    lines.append(f"Communication Style: {profile.get('communication_style', 'Neutral')} "
                 f"(confidence {profile.get('confidence', 0.0)})")
    triggers = profile.get("psychological_triggers", [])
    lines.append(f"Psychological Triggers: {', '.join(triggers) if triggers else '(none)'}")
    se = profile.get("social_engineering", [])
    lines.append(f"Claimed Persona: {', '.join(se) if se else '(none)'}")
    lines.append(f"Dominant Emotion: {profile.get('dominant_emotion', 'Neutral')}")
    urgency = profile.get("urgency", {})
    lines.append(f"Urgency: {urgency.get('level', 'Low')} (score {urgency.get('score', 0.0)})")
    lines.append(f"Persuasion: {', '.join(profile.get('persuasion', [])) or '(none)'}")
    lines.append(f"Manipulation: {profile.get('manipulation_level', 'Minimal')} "
                 f"(score {profile.get('manipulation_score', 0.0)})")
    lines.append(f"Overall Behavior: {profile.get('overall_behavior', '')}")
    return "\n".join(lines)
