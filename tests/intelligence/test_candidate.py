"""Tests for intelligence candidate engine."""

import pytest
from app.intelligence.enums import CandidateType, CandidateState, CandidateSource
from app.intelligence.models import ResearchCandidate
from app.intelligence.schemas import ResearchCandidateCreate
from app.intelligence.candidates import create_candidate, generate_unknown_ioc, generate_attribution_hypothesis, generate_contradiction
from app.intelligence.repository import create as repo_create, get, list_all


def test_candidate_model():
    c = ResearchCandidate(
        candidate_id="can-test",
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        reason="Test reason"
    )
    assert c.candidate_type == CandidateType.UNKNOWN_IOC
    assert c.status == CandidateState.NEW


def test_schema_validation():
    data = {
        "candidate_type": "UNKNOWN_IOC",
        "title": "Test",
        "description": "Desc",
        "source": "HUNTING",
        "reason": "Reason"
    }
    s = ResearchCandidateCreate(**data)
    assert s.candidate_type == CandidateType.UNKNOWN_IOC


def test_generate_unknown_ioc():
    import uuid
    ioc = f"example-{uuid.uuid4().hex[:8]}.com"
    cand = generate_unknown_ioc(ioc, CandidateSource.HUNTING)
    assert cand is not None
    assert cand.candidate_type == CandidateType.UNKNOWN_IOC
    assert cand.related_ioc_id == ioc


def test_deduplication():
    import uuid
    ioc = f"dup-{uuid.uuid4().hex[:8]}.com"
    c1 = generate_unknown_ioc(ioc, CandidateSource.HUNTING)
    assert c1 is not None
    c2 = generate_unknown_ioc(ioc, CandidateSource.HUNTING)
    assert c2 is None  # duplicate


def test_attribution_hypothesis():
    import uuid
    hid = f"hyp-{uuid.uuid4().hex[:8]}"
    cand = generate_attribution_hypothesis(hid, "Hypothesis description")
    assert cand is not None
    assert cand.candidate_type == CandidateType.ATTRIBUTION_HYPOTHESIS


def test_contradiction():
    import uuid
    claim = f"domain-{uuid.uuid4().hex[:8]}"
    cand = generate_contradiction(claim, "srcA", "srcB")
    assert cand is not None
    assert cand.candidate_type == CandidateType.CONTRADICTION
