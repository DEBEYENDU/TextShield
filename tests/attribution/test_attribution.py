"""Tests for attribution engine."""

from app.attribution.attribution_engine import AttributionEngine
from app.attribution.actor_profile import ActorProfiler
from app.attribution.infrastructure_intel import InfrastructureIntel


def test_engine_create():
    engine = AttributionEngine()
    assert engine is not None
    assert isinstance(engine.profiler, ActorProfiler)
    assert isinstance(engine.infra, InfrastructureIntel)


def test_analyze_message():
    engine = AttributionEngine()
    text = "Contact us at support@evil.example.com or visit http://evil.example.com/login"
    result = engine.analyze_message("msg1", text, campaign_id="camp1")
    assert result.message_id == "msg1"
    assert result.confidence >= 0
    assert len(result.infrastructure_links) > 0
    assert isinstance(result.explanation, str)


def test_actor_profile():
    profiler = ActorProfiler()
    profile = profiler.create_profile("a1", "Actor One", ["threat"])
    assert profile.id == "a1"
    updated = profiler.update_profile("a1", ttp_fp={"phishing": 0.8})
    assert updated.ttp_fingerprints.get("phishing") == 0.8


def test_infrastructure_ingest():
    infra = InfrastructureIntel()
    nodes = infra.ingest_message("m1", "Visit http://bad.com")
    assert len(nodes) >= 1
    assert nodes[0].type in ("url", "domain")
