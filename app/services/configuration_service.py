"""Configuration service: read-only view of effective settings."""

from __future__ import annotations

from typing import Any

from app.core.features import features
from app.core.settings import settings


def effective_config() -> dict[str, Any]:
    """Return the effective runtime configuration snapshot."""
    return {
        "environment": settings.ENVIRONMENT,
        "model_path": str(settings.MODEL_PATH),
        "vector_db_path": str(settings.VECTOR_DB_PATH),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "rag_enabled": features.rag_enabled,
        "llm_enabled": features.llm_enabled,
        "history_enabled": features.history_enabled,
        "history_store_preview": settings.HISTORY_STORE_PREVIEW,
        "max_message_length": settings.MAX_MESSAGE_LENGTH,
    }


def feature_flags() -> dict[str, bool]:
    """All feature-flag states."""
    return {
        "rag": features.rag_enabled,
        "llm": features.llm_enabled,
        "history": features.history_enabled,
        "evidence": features.evidence_enabled,
        "analytics": features.analytics_enabled,
    }
