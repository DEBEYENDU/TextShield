"""Threat graph configuration."""

from __future__ import annotations
from pydantic import BaseModel


class GraphConfig(BaseModel):
    max_graph_depth: int = 5
    max_neighbors: int = 100
    correlation_threshold: float = 0.6
    campaign_threshold: float = 0.7
    semantic_similarity_threshold: float = 0.75
    temporal_window_days: int = 30
    retention_days: int = 365
    privacy_hash: bool = True
    benign_protection: bool = True


config = GraphConfig()
