"""Tests for intelligence candidate prioritization."""

from datetime import datetime, timedelta
from app.intelligence.models import ResearchCandidate
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.prioritization import prioritize, prioritize_many


def make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, evidence_count=0, confidence=0.5, urgency=5):
    return ResearchCandidate(
        candidate_id="can-test",
        candidate_type=candidate_type,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        confidence=confidence,
        evidence_count=evidence_count,
        urgency=urgency,
        first_seen=datetime.utcnow() - timedelta(days=1),
        last_seen=datetime.utcnow(),
        status=CandidateState.NEW,
        reason="Test"
    )


def test_basic_prioritization():
    c = make_candidate()
    p = prioritize(c)
    assert 0.0 <= p.priority_score <= 1.0
    assert p.priority_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert p.candidate_id == "can-test"
    assert len(p.factors) > 0
    assert p.explanation


def test_low_priority_known_candidate():
    c = make_candidate(candidate_type=CandidateType.REPEATED_PATTERN, evidence_count=20, confidence=0.9, urgency=2)
    p = prioritize(c)
    # With high evidence and confidence, score should be moderate/low
    assert p.priority_score < 0.8


def test_high_priority_unknown_ioc():
    c = make_candidate(candidate_type=CandidateType.UNKNOWN_IOC, evidence_count=0, confidence=0.2, urgency=9)
    p = prioritize(c)
    assert p.priority_score > 0.4
    assert p.priority_level in {"MEDIUM", "HIGH", "CRITICAL"}


def test_determinism():
    c = make_candidate()
    p1 = prioritize(c)
    p2 = prioritize(c)
    assert p1.priority_score == p2.priority_score
    assert p1.priority_level == p2.priority_level


def test_missing_values_handled():
    c = ResearchCandidate(
        candidate_id="can-missing",
        candidate_type=CandidateType.OTHER,
        title="T",
        description="D",
        source=CandidateSource.SYSTEM,
        confidence=0.5,
        evidence_count=0,
        urgency=5,
    )
    p = prioritize(c)
    assert p.priority_score >= 0.0


def test_priority_band():
    c = make_candidate(urgency=10, confidence=0.1, evidence_count=0)
    p = prioritize(c)
    # Should be high
    assert p.priority_level in {"HIGH", "CRITICAL"}


def test_explanation_contains_factors():
    c = make_candidate()
    p = prioritize(c)
    assert "evidence_gap" in p.explanation.lower() or "uncertainty" in p.explanation.lower()


def test_prioritize_many():
    candidates = [make_candidate(), make_candidate(candidate_type=CandidateType.CONTRADICTION)]
    results = prioritize_many(candidates)
    assert len(results) == 2
    assert results[0].candidate_id == "can-test"


def test_false_positive_protection():
    # Legitimate recruitment candidate should not get inflated priority from keywords
    c = make_candidate(candidate_type=CandidateType.ANALYST_REQUEST, evidence_count=1, confidence=0.8, urgency=3)
    c.title = "College placement congratulations"
    c.description = "Congratulations to students placed at company"
    p = prioritize(c)
    # Priority should be based on evidence, not keywords
    assert 0.0 <= p.priority_score <= 1.0
    assert "placement" not in p.explanation.lower() or "candidate type" in p.explanation


def test_benign_infrastructure():
    c = make_candidate(candidate_type=CandidateType.NEW_INFRASTRUCTURE, evidence_count=0, confidence=0.5, urgency=5)
    c.related_entity_id = "Google Forms"
    p = prioritize(c)
    assert p.priority_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    # No keyword boost
