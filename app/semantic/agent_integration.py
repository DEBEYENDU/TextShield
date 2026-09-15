"""Agent integration for semantic insights."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticAgentIntegrator:
    def dispatch(self, text: str, semantic_result):
        try:
            from app.agents.orchestrator import agent_orchestrator
            task = {"type": "semantic_analysis", "text": text, "result": semantic_result.dict()}
            return agent_orchestrator.dispatch(task)
        except Exception as exc:
            logger.warning("Agent dispatch failed: %s", exc)
            return {"status": "failed", "error": str(exc)}
