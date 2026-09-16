"""Research configuration."""

from __future__ import annotations
from pydantic import BaseModel


class ResearchConfig(BaseModel):
    enabled: bool = True
    max_sources: int = 20
    max_depth: int = 3
    max_runtime_seconds: int = 600
    confidence_threshold: float = 0.6
    source_reliability_default: float = 0.5
    allow_external_sources: bool = False
    privacy_redact: bool = True
    max_evidence_items: int = 1000
    retention_days: int = 365


config = ResearchConfig()
