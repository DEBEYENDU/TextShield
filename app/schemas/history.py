"""Pydantic models: history contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.constants import CLASSIFICATION_VALUES, RISK_LEVELS


class HistoryEntry(BaseModel):
    id: int
    timestamp: str
    input_type: str
    message_hash: str
    classification: str
    confidence: float
    risk_level: str
    intent: str | None = None
    preview: str | None = None


class HistoryResponse(BaseModel):
    items: list[HistoryEntry]
    total: int
    limit: int
    offset: int


class HistoryFilters(BaseModel):
    """Optional query filters for the history list endpoint."""

    input_type: Literal["sms", "text", "email"] | None = None
    classification: Literal["SPAM", "HAM"] | None = Field(
        default=None, alias="classification"
    )
    risk_level: str | None = Field(default=None, pattern="|".join(RISK_LEVELS))
    intent: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

    model_config = {"extra": "forbid"}


HistoryDeleteResponse = dict
