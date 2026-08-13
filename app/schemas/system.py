"""Pydantic models: system, health and status contracts."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    model_ready: bool
    rag_ready: bool
    vector_db_backend: str
    embedding_provider: str
    llm_provider: str
    llm_model: str
    llm_available: bool
    history_rows: int


class ReadinessResponse(BaseModel):
    ready: bool
    components: dict[str, bool]
    message: str


class VersionResponse(BaseModel):
    name: str
    version: str
    tagline: str
    environment: str


class ConfigStatusResponse(BaseModel):
    environment: str
    model_path: str
    vector_db_path: str
    embedding_provider: str
    llm_provider: str
    llm_model: str
    rag_enabled: bool
    llm_enabled: bool
    history_enabled: bool
    history_store_preview: bool
    max_message_length: int


class AppStatusResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    feature_flags: dict[str, bool]
    model_ready: bool
    rag_ready: bool
    llm_available: bool


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class StatusResponse(BaseModel):
    success: bool
    data: Any = None
    message: str | None = None
    error: dict[str, Any] | None = None


class KBStatusResponse(BaseModel):
    ready: bool
    backend: str
    embedding_provider: str
    chunk_count: int
    document_count: int
    categories: list[str]
    built_at: str | None = None


class KBStatusDetail(KBStatusResponse):
    rebuild_ok: bool = False
    rebuild_message: str = ""
