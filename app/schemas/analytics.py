"""Pydantic models: analytics contract."""

from __future__ import annotations

from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_analyses: int
    spam_count: int
    ham_count: int
    spam_percentage: float
    average_confidence: float
    risk_distribution: dict
    message_type_distribution: dict
    intent_distribution: dict = {}
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
