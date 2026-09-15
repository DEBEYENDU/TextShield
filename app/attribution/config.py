"""Attribution configuration."""

from __future__ import annotations
from pydantic import BaseModel


class AttributionConfig(BaseModel):
    max_graph_depth: int = 5
    attribution_confidence_threshold: float = 0.6
    infrastructure_similarity_threshold: float = 0.75
    temporal_window_days: int = 90
    hypothesis_max_per_campaign: int = 10
    evidence_weight_ttps: float = 0.35
    evidence_weight_infrastructure: float = 0.30
    evidence_weight_linguistic: float = 0.20
    evidence_weight_temporal: float = 0.15
    privacy_hash: bool = True
    benign_protection: bool = True
    retention_days: int = 730


config = AttributionConfig()
