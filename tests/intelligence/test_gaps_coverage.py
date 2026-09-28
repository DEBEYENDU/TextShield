"""Tests for knowledge gap detection and coverage."""

from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate
from app.intelligence.gaps import detect_gaps_from_candidates, GapType, KnowledgeGap
from app.intelligence.coverage import calculate_coverage, overall_coverage, CoverageDomain
from datetime import datetime


def make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, description="Valid description with enough context", related_ioc_id=None, related_actor_id=None, evidence_count=0, confidence=0.5):
    return ResearchCandidate(
        candidate_id="can-test",
        candidate_type=candidate_type,
        title="Test",
        description=description,
        source=CandidateSource.HUNTING,
        related_ioc_id=related_ioc_id,
        related_actor_id=related_actor_id,
        evidence_count=evidence_count,
        confidence=confidence,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_missing_context_detection():
    c = make_candidate(candidate_type=CandidateType.REPEATED_PATTERN, description="Short")
    gaps = detect_gaps_from_candidates([c])
    assert len(gaps) == 1
    assert gaps[0].gap_type == GapType.MISSING_CONTEXT


def test_missing_ioc_detection():
    c = make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, related_ioc_id=None)
    gaps = detect_gaps_from_candidates([c])
    assert any(g.gap_type == GapType.MISSING_IOC for g in gaps)


def test_missing_attribution_detection():
    c = make_candidate(candidate_type=CandidateType.ATTRIBUTION_HYPOTHESIS, related_actor_id=None)
    gaps = detect_gaps_from_candidates([c])
    assert any(g.gap_type == GapType.MISSING_ATTRIBUTION for g in gaps)


def test_gap_deduplication():
    c = make_candidate(candidate_type=CandidateType.REPEATED_PATTERN, description="Short")
    gaps1 = detect_gaps_from_candidates([c, c])
    assert len(gaps1) == 1


def test_coverage_calculation():
    c1 = make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, evidence_count=1, confidence=0.8)
    c2 = make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, evidence_count=0, confidence=0.3)
    metrics = calculate_coverage([c1, c2], [])
    m = metrics[CoverageDomain.IOC]
    assert m.total_candidates == 2
    assert m.covered_candidates == 1
    assert 0.0 <= m.coverage_score <= 1.0


def test_overall_coverage():
    c = make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, evidence_count=1)
    metrics = calculate_coverage([c], [])
    score = overall_coverage(metrics)
    assert 0.0 <= score <= 1.0


def test_coverage_with_gaps():
    c = make_candidate(description="Short")
    gaps = detect_gaps_from_candidates([c])
    metrics = calculate_coverage([c], gaps)
    assert metrics[CoverageDomain.GENERAL].gap_count >= 0
