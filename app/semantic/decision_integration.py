"""Decision engine integration."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticDecisionIntegrator:
    def feed_decision(self, semantic_result, intent_result, behavior_result):
        try:
            from app.decision.engine import decision_engine
            inputs = {
                "semantic": semantic_result.dict(),
                "intent": intent_result,
                "behavior": behavior_result,
            }
            return decision_engine.decide(inputs)
        except Exception as exc:
            logger.warning("Decision integration failed: %s", exc)
            return {"decision": "unknown", "error": str(exc)}
