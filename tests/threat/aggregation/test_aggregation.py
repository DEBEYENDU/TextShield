from app.threat.aggregation import (
    AggregationEngine, ThreatProfile, EvidenceFuser,
    WeightedScorer, ConfidenceCalculator, ConflictDetector,
)


def test_aggregate_basic():
    engine = AggregationEngine()
    evidences = [
        {"provider": "google_safe_browsing", "threat_status": "malicious", "confidence": 0.8},
        {"provider": "virustotal", "threat_status": "malicious", "confidence": 0.9},
        {"provider": "openphish", "threat_status": "benign", "confidence": 0.4},
    ]
    profile = engine.aggregate(evidences)
    assert profile.evidence_count == 3
    assert profile.overall_threat_score > 0
    assert 0 <= profile.confidence <= 1
    assert profile.severity.name in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert isinstance(profile.provider_agreement, float)
    assert isinstance(profile.reasoning_summary, str)


def test_aggregate_all_malicious():
    from app.threat.aggregation.models import ThreatSeverity
    engine = AggregationEngine()
    evidences = [
        {"provider": "google_safe_browsing", "threat_status": "malicious", "confidence": 0.9},
        {"provider": "virustotal", "threat_status": "malicious", "confidence": 0.85},
    ]
    profile = engine.aggregate(evidences)
    assert profile.evidence_count == 2
    assert profile.overall_threat_score > 0.5
    assert profile.severity in (ThreatSeverity.HIGH, ThreatSeverity.CRITICAL)


def test_aggregate_all_benign():
    engine = AggregationEngine()
    evidences = [
        {"provider": "gsb", "threat_status": "benign", "confidence": 0.9},
        {"provider": "vt", "threat_status": "benign", "confidence": 0.85},
    ]
    profile = engine.aggregate(evidences)
    assert profile.evidence_count == 2
    assert profile.overall_threat_score < 0.3
    assert profile.severity.name in ("LOW", "MEDIUM")


def test_weighted_scorer():
    scorer = WeightedScorer()
    ev = [{"threat_status": "malicious", "confidence": 1.0}]
    score = scorer.score_evidence(ev, ["virustotal"])
    assert 0 <= score <= 1


def test_confidence_calculator():
    calc = ConfidenceCalculator()
    ev = [
        {"provider": "a", "threat_status": "malicious", "confidence": 0.9},
        {"provider": "b", "threat_status": "malicious", "confidence": 0.8},
    ]
    c = calc.calculate(ev)
    assert 0 <= c <= 1


def test_conflict_detector():
    det = ConflictDetector()
    ev = [
        {"provider": "a", "threat_status": "malicious", "confidence": 0.9},
        {"provider": "b", "threat_status": "benign", "confidence": 0.3},
    ]
    summary = det.detect(ev)
    assert "has_disagreement" in summary
    assert isinstance(summary["conflict_score"], float)


def test_fuser_fuse():
    fuser = EvidenceFuser()
    ev = [
        {"provider": "google_safe_browsing", "threat_status": "malicious", "confidence": 0.8},
        {"provider": "virustotal", "threat_status": "malicious", "confidence": 0.9},
    ]
    profile = fuser.fuse(ev)
    assert isinstance(profile, ThreatProfile)
    assert profile.evidence_count == 2
    assert profile.overall_threat_score >= 0


def test_fuser_fuse_with_reliability():
    fuser = EvidenceFuser()
    ev = [
        {"provider": "google_safe_browsing", "threat_status": "malicious", "confidence": 0.8},
        {"provider": "virustotal", "threat_status": "malicious", "confidence": 0.9},
    ]
    profile = fuser.fuse(ev, provider_reliability={"google_safe_browsing": 0.9, "virustotal": 0.8})
    assert isinstance(profile, ThreatProfile)
    assert profile.reliability_score > 0


def test_profile_to_from_dict():
    from app.threat.aggregation.models import ThreatSeverity
    profile = ThreatProfile(
        overall_threat_score=0.7,
        confidence=0.8,
        severity=ThreatSeverity.HIGH,
        provider_agreement=0.8,
        evidence_count=3,
        reliability_score=0.85,
        reasoning_summary="test reasoning",
    )
    d = profile.to_dict()
    profile2 = ThreatProfile.from_dict(d)
    assert profile2.overall_threat_score == profile.overall_threat_score
    assert profile2.confidence == profile.confidence