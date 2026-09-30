"""Knowledge governance lifecycle."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class GovernanceState(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"
    EXPIRED = "EXPIRED"


class KnowledgeGovernanceRecord(BaseModel):
    governance_id: str = Field(default_factory=lambda: f"gvt-{uuid.uuid4().hex[:8]}")
    entity_id: Optional[str] = None
    candidate_id: Optional[str] = None
    state: GovernanceState = GovernanceState.DRAFT
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewer_id: Optional[str] = None
    notes: str = ""
    metadata: dict = Field(default_factory=dict)


def create_governance_record(candidate, initial_state: GovernanceState = GovernanceState.DRAFT) -> KnowledgeGovernanceRecord:
    return KnowledgeGovernanceRecord(
        entity_id=candidate.related_entity_id or candidate.related_ioc_id,
        candidate_id=candidate.candidate_id,
        state=initial_state,
        confidence=getattr(candidate, "confidence", 0.5),
        evidence_count=getattr(candidate, "evidence_count", 0)
    )


def promote(record: KnowledgeGovernanceRecord, reviewer_id: Optional[str] = None) -> KnowledgeGovernanceRecord:
    if record.state == GovernanceState.PENDING_REVIEW and record.confidence >= 0.7 and record.evidence_count >= 2:
        record.state = GovernanceState.APPROVED
    elif record.state == GovernanceState.DRAFT and record.confidence >= 0.8:
        record.state = GovernanceState.PENDING_REVIEW
    record.reviewer_id = reviewer_id
    record.updated_at = datetime.utcnow()
    return record


def demote(record: KnowledgeGovernanceRecord, reason: str = "") -> KnowledgeGovernanceRecord:
    if record.state == GovernanceState.APPROVED:
        record.state = GovernanceState.DEPRECATED
        record.notes = reason or "Demoted due to new evidence"
    record.updated_at = datetime.utcnow()
    return record


def expire(record: KnowledgeGovernanceRecord, max_age_days: int = 365) -> KnowledgeGovernanceRecord:
    age = (datetime.utcnow() - record.created_at).days
    if age > max_age_days and record.state in (GovernanceState.APPROVED, GovernanceState.DEPRECATED):
        record.state = GovernanceState.EXPIRED
    record.updated_at = datetime.utcnow()
    return record


def is_approved(record: KnowledgeGovernanceRecord) -> bool:
    return record.state == GovernanceState.APPROVED


def review_queue(records: List[KnowledgeGovernanceRecord]) -> List[KnowledgeGovernanceRecord]:
    return [r for r in records if r.state == GovernanceState.PENDING_REVIEW]
