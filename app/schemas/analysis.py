"""Pydantic models for the TextShield REST API.

All user input is validated here: type constraints, length limits and
content-presence rules. Requests failing validation produce HTTP 422.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.config import settings

_MAX_LEN = settings.MAX_MESSAGE_LENGTH


class AnalyzeRequest(BaseModel):
    """Input accepted by POST /api/analyze.

    Either ``message`` (SMS/TEXT) or an email combination
    (``subject`` / ``sender`` / ``body``) or a raw pasted email
    (``email_raw``) must be provided.
    """

    input_type: Literal["sms", "text", "email"] = "text"
    message: str | None = Field(
        default=None, max_length=_MAX_LEN, min_length=1,
        description="Full message text for SMS/TEXT input types.",
    )
    subject: str | None = Field(default=None, max_length=500)
    sender: str | None = Field(default=None, max_length=500)
    body: str | None = Field(default=None, max_length=_MAX_LEN)
    email_raw: str | None = Field(default=None, max_length=_MAX_LEN * 2)

    @model_validator(mode="after")
    def _ensure_content(self) -> "AnalyzeRequest":
        has_something = bool(
            (self.message or "").strip()
            or (self.body or "").strip()
            or (self.email_raw or "").strip()
        )
        if not has_something:
            raise ValueError("Provide at least one of: message, body, email_raw")
        return self


class AnalysisResult(BaseModel):
    classification: str
    confidence: float
    risk_level: str
    message_type: str
    indicators: list[dict] = Field(default_factory=list)
    urls: list[dict] = Field(default_factory=list)
    rag_evidence: list[dict] = Field(default_factory=list)
    explanation: str
    explanation_source: Literal["llm", "template"]
    recommended_action: str
    risk_factors: list[str] = Field(default_factory=list)
    model_used: str
    rag_status: dict = Field(default_factory=dict)
    disclaimer: str = (
        "This analysis is informational and reflects static pattern analysis. "
        "It is not legal, financial or security assurance."
    )


class HistoryEntry(BaseModel):
    id: int
    timestamp: str
    input_type: str
    message_hash: str
    classification: str
    confidence: float
    risk_level: str
    preview: str | None = None


class HistoryResponse(BaseModel):
    items: list[HistoryEntry]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_analyses: int
    spam_count: int
    ham_count: int
    spam_percentage: float
    average_confidence: float
    risk_distribution: dict
    message_type_distribution: dict
    analyses_per_day: list[dict]
    latest_analysis_at: str | None


class ModelInfoResponse(BaseModel):
    available: bool
    algorithm: str | None = None
    trained_at: str | None = None
    dataset: dict | None = None
    label_mapping: dict | None = None
    metrics: dict | None = None
    comparison: dict | None = None
    message: str | None = None


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