"""Intelligence candidate schemas."""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from .enums import CandidateType, CandidateState, CandidateSource


class ResearchCandidateCreate(BaseModel):
    candidate_type: CandidateType
    title: str
    description: str
    source: CandidateSource
    source_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    urgency: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)
    research_scope: str = "general"
    related_analysis_id: Optional[str] = None
    related_finding_id: Optional[str] = None
    related_campaign_id: Optional[str] = None
    related_entity_id: Optional[str] = None
    related_ioc_id: Optional[str] = None
    related_research_id: Optional[str] = None
    related_actor_id: Optional[str] = None
    reason: str = ""


class ResearchCandidateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=10)
    urgency: Optional[int] = Field(default=None, ge=1, le=10)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_count: Optional[int] = Field(default=None, ge=0)
    status: Optional[CandidateState] = None
    reason: Optional[str] = None


class ResearchCandidateResponse(BaseModel):
    candidate_id: str
    candidate_type: CandidateType
    title: str
    description: str
    source: CandidateSource
    status: CandidateState
    priority: int
    confidence: float
    evidence_count: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
