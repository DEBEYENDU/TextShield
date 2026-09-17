"""Hunting configuration."""

from __future__ import annotations
from pydantic import BaseModel


class HuntingConfig(BaseModel):
    enabled: bool = True
    max_observations: int = 100000
    time_windows: list[int] = [1, 6, 24, 168, 720, 2160]  # hours
    anomaly_threshold_z: float = 2.5
    clustering_threshold: float = 0.75
    semantic_similarity_threshold: float = 0.75
    pattern_min_occurrences: int = 3
    finding_retention_days: int = 365
    scheduler_interval_hours: int = 24
    worker_limits: int = 4
    timeout_seconds: int = 600
    privacy_redact: bool = True
    benign_infrastructure_protection: bool = True


config = HuntingConfig()
