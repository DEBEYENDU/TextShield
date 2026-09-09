"""Understanding pipeline — the v4 pre-classification orchestrator.

Incoming Message -> Language -> Message Type -> Intent -> Entities ->
Threat Indicators -> Legitimacy Indicators -> Evidence Summary -> Profile.

Design: regex/semantic scoring only (no model loads), singleton reuse,
graceful degradation per stage. Overhead target: < 300 ms.
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.semantic.semantic_pipeline import SemanticPipeline
from app.understanding import evidence as evidence_mod
from app.understanding import profile as profile_mod
from app.understanding.entities import entity_extractor
from app.understanding.intent_detector import intent_detector
from app.understanding.language import detect_language_info
from app.understanding.legitimacy import legitimacy_engine
from app.understanding.message_type import message_type_classifier
from app.understanding.threat import threat_engine

logger = get_logger(__name__)

_semantic: SemanticPipeline | None = None


def _semantic_pipeline() -> SemanticPipeline:
    global _semantic
    if _semantic is None:
        _semantic = SemanticPipeline()
    return _semantic


class UnderstandingPipeline:
    """Run all understanding stages; never raises, never classifies."""

    engine_version = "4.0.0"

    def analyze(self, text: str, sender: str = "", subject: str = "") -> dict:
        started = time.perf_counter()
        full = " ".join(p for p in (subject, text, sender) if p).strip() if subject else (text or "")
        result: dict = {"engine_version": self.engine_version}
        try:
            result["language"] = detect_language_info(full)
        except Exception as exc:
            logger.warning("understanding language stage failed: %s", exc)
            result["language"] = {"language": "unknown", "confidence": 0.0}
        try:
            contexts: list = []
            try:
                contexts = _semantic_pipeline().detect_contexts(full)
            except Exception:
                pass
            result["message_type"] = message_type_classifier.classify(full, contexts=contexts)
        except Exception as exc:
            logger.warning("understanding type stage failed: %s", exc)
            result["message_type"] = {"type": "Unknown", "confidence": 0.0, "evidence": []}
        try:
            result["intent"] = intent_detector.detect(full)
        except Exception as exc:
            logger.warning("understanding intent stage failed: %s", exc)
            result["intent"] = {"intent": "Inform", "confidence": 0.0, "reasoning": "stage error"}
        try:
            result["entities"] = entity_extractor.extract(text or "", sender=sender)
        except Exception as exc:
            logger.warning("understanding entity stage failed: %s", exc)
            result["entities"] = {"total_count": 0}
        try:
            threat = threat_engine.analyze(full)
        except Exception as exc:
            logger.warning("understanding threat stage failed: %s", exc)
            threat = {"threat_score": 0.0, "indicators": [], "count": 0, "families": []}
        try:
            legitimacy = legitimacy_engine.analyze(full)
        except Exception as exc:
            logger.warning("understanding legitimacy stage failed: %s", exc)
            legitimacy = {"trust_score": 0.0, "indicators": [], "count": 0}
        result["threat"] = threat
        result["legitimacy"] = legitimacy
        try:
            result["evidence"] = evidence_mod.evidence_model.build(threat, legitimacy)
        except Exception as exc:
            logger.warning("understanding evidence stage failed: %s", exc)
            result["evidence"] = {"threat_indicators": [], "legitimacy_indicators": [],
                                  "threat_score": 0.0, "trust_score": 0.0,
                                  "evidence_lean": "mixed", "summary_text": ""}
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        try:
            result["profile"] = profile_mod.message_profile.build(
                result["language"], result["message_type"], result["intent"],
                result["entities"], result["evidence"], elapsed_ms)
        except Exception as exc:
            logger.warning("understanding profile stage failed: %s", exc)
            result["profile"] = {"category": "Unknown", "intent": "Inform",
                                 "threat_score": 0.0, "trust_score": 0.0, "risk": "Low"}
        result["latency_ms"] = round(elapsed_ms, 2)
        return result


understanding_pipeline = UnderstandingPipeline()

__all__ = ["UnderstandingPipeline", "understanding_pipeline"]
