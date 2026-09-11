"""Pydantic schemas for the threat-intel dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    ioc: str = Field(..., min_length=3, max_length=2048)
    ioc_type: str | None = None
    providers: list[str] | None = None


class ProviderInfo(BaseModel):
    name: str
    version: str
    enabled: bool
    configured: bool
    capabilities: list[str] = Field(default_factory=list)


class AggregatedResponse(BaseModel):
    ioc: str
    ioc_type: str
    results: list[dict] = Field(default_factory=list)
    aggregated_verdict: str = "unknown"
    confidence: float = 0.0
    cached: bool = False
