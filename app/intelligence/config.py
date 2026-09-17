"""Intelligence configuration."""

from __future__ import annotations
from pydantic import BaseModel


class IntelligenceConfig(BaseModel):
    enabled: bool = True
    candidates_enabled: bool = True
    max_candidates: int = 10000
    candidate_retention_days: int = 365
    deduplication_enabled: bool = True


config = IntelligenceConfig()
