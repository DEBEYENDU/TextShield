"""System status service: lifecycle, health and status snapshots."""
from __future__ import annotations

import time
from typing import Any

from app import __version__
from app.core.logging import get_logger
from app.core.settings import settings
from app.rag.llm import create_llm_client
from app.rag.retriever import retriever
from app.services import configuration_service, history_service, models_service

logger = get_logger(__name__)

STARTED_AT = time.monotonic()
START_TIME_ISO: str | None = None


def mark_started() -> None:
    """Record the application boot timestamp (called at startup)."""
    global START_TIME_ISO
    from app.utils.date_utils import utc_now_iso

    START_TIME_ISO = utc_now_iso()


def uptime_seconds() -> float:
    return round(time.monotonic() - STARTED_AT, 2)


def health() -> dict[str, Any]:
    """Service health: model, RAG and LLM availability."""
    model_ready = models_service.is_available()
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
        "history_rows": history_service.count_rows(),
    }


def readiness() -> dict[str, Any]:
    """Readiness: DB reachable and migrations applied."""
    try:
        history_service.count_rows()
        components = {"database": True, "migrations": True}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Readiness probe failed: %s", exc)
        return {"ready": False, "components": {"database": False}, "message": "Database unavailable"}
    return {"ready": True, "components": components, "message": "ready"}


def app_status() -> dict[str, Any]:
    """Application status snapshot (status/version/uptime/flags)."""
    return {
        "status": "running",
        "version": __version__,
        "uptime_seconds": uptime_seconds(),
        "feature_flags": configuration_service.feature_flags(),
        "model_ready": models_service.is_available(),
        "rag_ready": retriever.status().get("ready", False),
        "llm_available": create_llm_client() is not None,
    }