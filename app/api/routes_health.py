"""Route module: health, knowledge-base status and rebuild."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from app import __version__
from app.core.logging import get_logger
from app.core.config import settings
from app.database import database as db
from app.rag.llm import create_llm_client
from app.rag.retriever import retriever
from app.schemas.analysis import HealthResponse, KBStatusResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    """Service health: model, RAG and LLM availability."""
    model_ready = settings.MODEL_PATH.exists() and settings.VECTORIZER_PATH.exists()
    llm_client = create_llm_client()
    rag_status = retriever.status()
    return {
        "status": "ok" if model_ready else "degraded",
        "version": __version__,
        "model_ready": model_ready,
        "rag_ready": rag_status["ready"],
        "vector_db_backend": rag_status["backend"],
        "embedding_provider": rag_status["embedding_provider"],
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_available": llm_client is not None,
        "history_rows": db.query_history(limit=1)[1],
    }


@router.get("/knowledge-base", response_model=KBStatusResponse)
def knowledge_base_status() -> dict:
    """Knowledge base build status (no rebuild)."""
    return retriever.status()


@router.post("/knowledge-base/rebuild", response_model=KBStatusResponse)
def rebuild_knowledge_base() -> dict:
    """Rebuild the vector database from the knowledge_base directory."""
    try:
        from scripts.build_knowledge_base import build

        info = build()
        retriever.invalidate_cache()
        logger.info("Knowledge base rebuilt: %s", info.get("chunk_count"))
        return {
            "ready": True,
            "backend": info.get("backend", ""),
            "embedding_provider": info.get("embedding_provider", ""),
            "chunk_count": info.get("chunk_count", 0),
            "document_count": info.get("document_count", 0),
            "categories": info.get("categories", []),
            "built_at": info.get("built_at"),
        }
    except Exception as exc:
        logger.error("Knowledge base rebuild failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {exc}") from exc