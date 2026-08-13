"""Pydantic models: analysis contract (request + response).

All user input is validated here: type constraints, length limits and
content-presence rules. Requests failing validation produce HTTP 422.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.constants import EXPLANATION_SOURCE_TEMPLATE
from app.core.settings import settings

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
    risk_score: float
    risk_level: str
    message_type: str
    intent: dict = Field(default_factory=dict)
    indicators: list[dict] = Field(default_factory=list)
    urls: list[dict] = Field(default_factory=list)
    rag_evidence: list[dict] = Field(default_factory=list)
    explanation: str
    explanation_source: Literal["llm", EXPLANATION_SOURCE_TEMPLATE]
    recommended_action: str
    risk_factors: list[str] = Field(default_factory=list)
    model_used: str
    rag_status: dict = Field(default_factory=dict)
    disclaimer: str = (
        "This analysis is informational and reflects static pattern analysis. "
        "It is not legal, financial or security assurance."
    )
