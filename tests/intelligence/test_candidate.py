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
    cand = generate_unknown_ioc("example.com", CandidateSource.HUNTING)
    assert cand is not None
    assert cand.candidate_type == CandidateType.UNKNOWN_IOC
    assert cand.related_ioc_id == "example.com"


def test_deduplication():
    c1 = generate_unknown_ioc("dup.com", CandidateSource.HUNTING)
    assert c1 is not None
    c2 = generate_unknown_ioc("dup.com", CandidateSource.HUNTING)
    assert c2 is None  # duplicate


def test_attribution_hypothesis():
    cand = generate_attribution_hypothesis("hyp-1", "Hypothesis description")
    assert cand is not None
    assert cand.candidate_type == CandidateType.ATTRIBUTION_HYPOTHESIS


def test_contradiction():
    cand = generate_contradiction("domain malicious", "srcA", "srcB")
    assert cand is not None
    assert cand.candidate_type == CandidateType.CONTRADICTION
