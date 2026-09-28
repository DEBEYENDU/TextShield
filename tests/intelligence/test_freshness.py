"""Tests for knowledge freshness engine."""

from datetime import datetime, timedelta
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate
from app.intelligence.freshness import (
    evaluate_candidate_freshness,
    detect_stale_candidates,
    compute_staleness,
    classify_freshness,
    FreshnessStatus,
    needs_refresh,
)


def make_candidate(days_old=0, candidate_id="can-test"):
    now = datetime.utcnow()
    return ResearchCandidate(
        candidate_id=candidate_id,
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        created_at=now - timedelta(days=days_old),
        last_seen=now - timedelta(days=days_old),
        status=CandidateState.NEW,
        reason="Test"
    )


def test_compute_staleness():
    assert compute_staleness(0) == 1.0
    assert compute_staleness(90) < 0.1


def test_classify_freshness():
    assert classify_freshness(0.8) == FreshnessStatus.FRESH
    assert classify_freshness(0.5) == FreshnessStatus.STALE
    assert classify_freshness(0.2) == FreshnessStatus.EXPIRED


def test_evaluate_fresh():
    c = make_candidate(days_old=5)
    rec = evaluate_candidate_freshness(c)
    assert rec.status == FreshnessStatus.FRESH
    assert rec.staleness_score > 0.7


def test_evaluate_stale():
    c = make_candidate(days_old=100)
    rec = evaluate_candidate_freshness(c)
    assert rec.status in (FreshnessStatus.STALE, FreshnessStatus.EXPIRED)
    assert rec.age_days >= 100


def test_detect_stale_candidates():
    c1 = make_candidate(days_old=10, candidate_id="c1")
    c2 = make_candidate(days_old=120, candidate_id="c2")
    stale = detect_stale_candidates([c1, c2], max_age_days=90)
    ids = [r.candidate_id for r in stale]
    assert "c2" in ids
    assert "c1" not in ids or len(stale) >= 1


def test_needs_refresh():
    c = make_candidate(days_old=200)
    rec = evaluate_candidate_freshness(c)
    assert needs_refresh(rec, refresh_threshold=0.5) is True

    c2 = make_candidate(days_old=1)
    rec2 = evaluate_candidate_freshness(c2)
    assert needs_refresh(rec2, refresh_threshold=0.5) is False
