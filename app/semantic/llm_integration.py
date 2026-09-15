"""LLM integration for semantic explanation."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticLLMIntegrator:
    def explain(self, text: str, semantic_result):
        try:
            from app.llm.client import llm_client
            prompt = f"Explain semantic analysis for: {text[:200]}"
            explanation = llm_client.generate(prompt)
            return {"semantic": semantic_result, "explanation": explanation}
        except Exception as exc:
            logger.warning("LLM explanation failed: %s", exc)
            return {"semantic": semantic_result, "explanation": None}
