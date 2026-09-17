from app.evidence.engine import EvidenceEngine
from app.evidence.registry import get_registry, register_evidence_source
from app.evidence.models import EvidenceItem, EvidenceSource


def test_evidence_engine_collect():
    engine = EvidenceEngine()
    # register a dummy source
    register_evidence_source("test_source", EvidenceSource.THREAT_INTELLIGENCE)
    merged = engine.collect("analysis_001")
    assert merged is not None
    assert merged.evidence_id is not None
    assert merged.source == EvidenceSource.THREAT_INTELLIGENCE


def test_evidence_engine_get():
    engine = EvidenceEngine()
    merged = engine.collect("analysis_002")
    retrieved = engine.get_evidence("analysis_002")
    assert retrieved is not None
    assert retrieved.evidence_id == merged.evidence_id


def test_evidence_engine_graph():
    engine = EvidenceEngine()
    register_evidence_source("test_src", EvidenceSource.THREAT_INTELLIGENCE)
    merged = engine.collect("analysis_003")
    graph = engine.get_graph("analysis_003")
    assert graph is not None
    assert graph.all_nodes() is not None


def test_evidence_explanation():
    from app.evidence.explanation import EvidenceExplanation
    engine = EvidenceEngine()
    register_evidence_source("test_s", EvidenceSource.THREAT_INTELLIGENCE)
    merged = engine.collect("analysis_004")
    summary = EvidenceExplanation.evidence_summary(merged)
    assert "THREAT_INTELLIGENCE" in summary or "threat_intelligence" in summary.lower()


def test_evidence_validator():
    from app.evidence.validator import EvidenceValidator
    item = EvidenceItem(
        source="invalid_source",
        confidence=1.5,  # out of range
        summary="test",
    )
    errors = EvidenceValidator.validate(item)
    assert len(errors) > 0  # should have errors


def test_evidence_merger():
    from app.evidence.merger import EvidenceMerger
    from app.evidence.models import EvidenceSource
    merger = EvidenceMerger()
    items = [
        EvidenceItem(source=EvidenceSource.THREAT_INTELLIGENCE, confidence=0.8, summary="first"),
        EvidenceItem(source=EvidenceSource.THREAT_INTELLIGENCE, confidence=0.9, summary="second"),
    ]
    merged = merger.merge(items)
    assert merged is not None
    assert merged.confidence > 0