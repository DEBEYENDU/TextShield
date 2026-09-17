"""Job models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Job(BaseModel):
    job_id: str
    analysis_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt_count: int = 0
    priority: str = "NORMAL"
    source: str = "api"
    channel: str = "unknown"
    error_code: Optional[str] = None
    result_reference: Optional[str] = None
