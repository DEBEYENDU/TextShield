"""Detection proposal workflow."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DetectionProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    DEPLOYED = "DEPLOYED"
    REJECTED = "REJECTED"


class DetectionProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"det-{uuid.uuid4().hex[:8]}")
    candidate_id: Optional[str] = None
    title: str
    description: str
    rule_logic: str
    severity: int = Field(default=5, ge=1, le=10)
    status: DetectionProposalStatus = DetectionProposalStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


def create_proposal(candidate, title: str, rule_logic: str) -> DetectionProposal:
    return DetectionProposal(
        candidate_id=candidate.candidate_id,
        title=title,
        description=candidate.description,
        rule_logic=rule_logic,
        severity=int(candidate.priority)
    )


def review_proposal(proposal: DetectionProposal) -> DetectionProposal:
    if proposal.status == DetectionProposalStatus.DRAFT:
        proposal.status = DetectionProposalStatus.REVIEW
    proposal.updated_at = datetime.utcnow()
    return proposal


def approve_proposal(proposal: DetectionProposal) -> DetectionProposal:
    if proposal.status == DetectionProposalStatus.REVIEW:
        proposal.status = DetectionProposalStatus.APPROVED
    proposal.updated_at = datetime.utcnow()
    return proposal


def deploy_proposal(proposal: DetectionProposal) -> DetectionProposal:
    if proposal.status == DetectionProposalStatus.APPROVED:
        proposal.status = DetectionProposalStatus.DEPLOYED
    proposal.updated_at = datetime.utcnow()
    return proposal


def list_proposals_by_status(proposals: List[DetectionProposal], status: DetectionProposalStatus) -> List[DetectionProposal]:
    return [p for p in proposals if p.status == status]
