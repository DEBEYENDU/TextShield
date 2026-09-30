"""Tests for knowledge governance."""

from datetime import datetime, timedelta
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate
from app.intelligence.governance import (
    KnowledgeGovernanceRecord,
    GovernanceState,
    create_governance_record,
    promote,
    demote,
    expire,
    is_approved,
    review_queue,
)
from app.intelligence.promotion import should_promote, promote_candidate
from app.intelligence.expiration import expire_records, is_expired


def make_candidate(confidence=0.5, evidence_count=0, candidate_id="can-test"):
    return ResearchCandidate(
        candidate_id=candidate_id,
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        confidence=confidence,
        evidence_count=evidence_count,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_create_governance():
    c = make_candidate()
    rec = create_governance_record(c)
    assert rec.candidate_id == c.candidate_id
    assert rec.state == GovernanceState.DRAFT


def test_promote_to_pending():
    c = make_candidate(confidence=0.85, evidence_count=1)
    rec = create_governance_record(c)
    rec = promote_candidate(rec)
    assert rec.state == GovernanceState.PENDING_REVIEW


def test_promote_to_approved():
    rec = KnowledgeGovernanceRecord(
        candidate_id="c1",
        state=GovernanceState.PENDING_REVIEW,
        confidence=0.75,
        evidence_count=3
    )
    rec = promote(rec)
    assert rec.state == GovernanceState.APPROVED
    assert is_approved(rec)


def test_demote():
    rec = KnowledgeGovernanceRecord(candidate_id="c1", state=GovernanceState.APPROVED)
    rec = demote(rec, reason="Conflict")
    assert rec.state == GovernanceState.DEPRECATED


def test_expire():
    rec = KnowledgeGovernanceRecord(
        candidate_id="c1",
        state=GovernanceState.APPROVED,
        created_at=datetime.utcnow() - timedelta(days=400)
    )
    rec = expire(rec, max_age_days=365)
    assert rec.state == GovernanceState.EXPIRED


def test_should_promote():
    rec = KnowledgeGovernanceRecord(candidate_id="c1", state=GovernanceState.DRAFT, confidence=0.9, evidence_count=1)
    assert should_promote(rec) is True
    rec2 = KnowledgeGovernanceRecord(candidate_id="c1", state=GovernanceState.DRAFT, confidence=0.6, evidence_count=1)
    assert should_promote(rec2) is False


def test_expire_records():
    rec1 = KnowledgeGovernanceRecord(candidate_id="c1", state=GovernanceState.APPROVED, created_at=datetime.utcnow() - timedelta(days=400))
    rec2 = KnowledgeGovernanceRecord(candidate_id="c2", state=GovernanceState.APPROVED, created_at=datetime.utcnow() - timedelta(days=10))
    count = expire_records([rec1, rec2], max_age_days=365)
    assert count == 1
    assert rec1.state == GovernanceState.EXPIRED


def test_review_queue():
    rec1 = KnowledgeGovernanceRecord(candidate_id="c1", state=GovernanceState.PENDING_REVIEW)
    rec2 = KnowledgeGovernanceRecord(candidate_id="c2", state=GovernanceState.DRAFT)
    q = review_queue([rec1, rec2])
    assert len(q) == 1
    assert q[0].candidate_id == "c1"
