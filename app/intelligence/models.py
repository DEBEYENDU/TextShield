"""Intelligence candidate data models."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from .enums import CandidateType, CandidateState, CandidateSource


class ResearchCandidate(BaseModel):
    candidate_id: str
    candidate_type: CandidateType
    title: str
    description: str
    source: CandidateSource
    source_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    urgency: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    status: CandidateState = CandidateState.NEW
    research_scope: str = "general"
    related_analysis_id: Optional[str] = None
    related_finding_id: Optional[str] = None
    related_campaign_id: Optional[str] = None
    related_entity_id: Optional[str] = None
    related_ioc_id: Optional[str] = None
    related_research_id: Optional[str] = None
    related_actor_id: Optional[str] = None
    reason: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = {}
