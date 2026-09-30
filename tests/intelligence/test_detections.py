"""Tests for detection proposals."""

from app.intelligence.detections import (
    DetectionProposal,
    DetectionProposalStatus,
    create_proposal,
    review_proposal,
    approve_proposal,
    deploy_proposal,
    list_proposals_by_status
)
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate


def make_candidate():
    return ResearchCandidate(
        candidate_id="can-1",
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Detect unknown IOC",
        source=CandidateSource.HUNTING,
        priority=7,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_create_proposal():
    c = make_candidate()
    p = create_proposal(c, "Detect IOC", "rule...")
    assert p.candidate_id == "can-1"
    assert p.status == DetectionProposalStatus.DRAFT
    assert p.severity == 7


def test_review_flow():
    c = make_candidate()
    p = create_proposal(c, "t", "r")
    p = review_proposal(p)
    assert p.status == DetectionProposalStatus.REVIEW
    p = approve_proposal(p)
    assert p.status == DetectionProposalStatus.APPROVED
    p = deploy_proposal(p)
    assert p.status == DetectionProposalStatus.DEPLOYED


def test_list_by_status():
    p1 = DetectionProposal(proposal_id="p1", title="a", description="d", rule_logic="r", status=DetectionProposalStatus.DRAFT)
    p2 = DetectionProposal(proposal_id="p2", title="b", description="d", rule_logic="r", status=DetectionProposalStatus.APPROVED)
    drafts = list_proposals_by_status([p1, p2], DetectionProposalStatus.DRAFT)
    assert len(drafts) == 1
    assert drafts[0].proposal_id == "p1"
