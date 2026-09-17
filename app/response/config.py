"""Response engine configuration."""

from __future__ import annotations
from pydantic import BaseModel


class ResponseConfig(BaseModel):
    enabled: bool = True
    mode: str = "RECOMMEND_ONLY"  # DISABLED, RECOMMEND_ONLY, AUTO_LOW_RISK, AUTO_MEDIUM_RISK, AUTO_HIGH_CONFIDENCE
    default_policy: str = "CONSERVATIVE"
    require_approval: bool = True
    max_scope: str = "MESSAGE"
    auto_quarantine_threshold: float = 0.85
    auto_block_threshold: float = 0.95
    action_timeout_seconds: int = 300
    action_retention_days: int = 365
    dry_run: bool = False
    notification_enabled: bool = True
    approval_timeout_hours: int = 24


config = ResponseConfig()
