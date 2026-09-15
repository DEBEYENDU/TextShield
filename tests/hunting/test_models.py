"""Tests for hunting models."""

from app.hunting.models import Observation, Finding, Pattern
from app.hunting.enums import FindingState, FindingType
from datetime import datetime


def test_observation_model():
    obs = Observation(
        observation_id="o1",
        analysis_id="a1",
        message_id="m1",
        timestamp=datetime.utcnow(),
        channel="email"
    )
    assert obs.observation_id == "o1"


def test_finding_model():
    f = Finding(
        finding_id="f1",
        finding_type=FindingType.IOC_REUSE,
        state=FindingState.NEW,
        score=0.7,
        confidence=0.6,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    assert f.state == FindingState.NEW


def test_pattern_model():
    p = Pattern(
        pattern_id="p1",
        pattern_type="domain_reuse",
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    assert p.occurrence_count == 0
