"""Graph data models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GraphNode(BaseModel):
    id: str
    type: str
    normalized_value: str
    display_value: str
    confidence: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    observation_count: int = 0
    active: bool = True


class GraphEdge(BaseModel):
    src_id: str
    dst_id: str
    rel_type: str
    confidence: float = 0.0
    created_at: Optional[datetime] = None
    evidence: str = ""


class Campaign(BaseModel):
    id: str
    name: str
    type: str
    confidence: float = 0.0
    created_at: datetime
    updated_at: datetime
    status: str = "DETECTED"
    correlation_score: float = 0.0
    evidence: list[str] = []
