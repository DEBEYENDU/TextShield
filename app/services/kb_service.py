"""Knowledge-base service: status and rebuild orchestration."""
from __future__ import annotations

from typing import Any

from app.core.exceptions import KnowledgeBaseError
from app.core.logging import get_logger
from app.rag.retriever import retriever

logger = get_logger(__name__)


def status() -> dict[str, Any]:
    """Current knowledge-base status (no rebuild)."""
    return retriever.status()


def rebuild() -> dict[str, Any]:
    """Rebuild the vector database from the knowledge_base directory."""
    try:
        from scripts.build_knowledge_base import build

        info = build()
        retriever.invalidate_cache()
        logger.info(
            "Knowledge base rebuilt: %s chunks, %s documents",
            info.get("chunk_count"),
            info.get("document_count"),
        )
        return {
            "ready": True,
            "backend": info.get("backend", ""),
            "embedding_provider": info.get("embedding_provider", ""),
            "chunk_count": info.get("chunk_count", 0),
            "document_count": info.get("document_count", 0),
            "categories": info.get("categories", []),
            "built_at": info.get("built_at"),
        }
    except KnowledgeBaseError:
        raise
    except Exception as exc:
        logger.error("Knowledge base rebuild failed: %s", exc)
        raise KnowledgeBaseError(f"Rebuild failed: {exc}") from exc