"""RAG integration for semantic context enrichment."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticRAGIntegrator:
    def enrich(self, text: str, semantic_result):
        try:
            from app.rag.knowledge_base import knowledge_base
            enriched = knowledge_base.search(text, top_k=3)
            return {"semantic": semantic_result, "rag_hits": enriched}
        except Exception as exc:
            logger.warning("RAG enrichment failed: %s", exc)
            return {"semantic": semantic_result, "rag_hits": []}
