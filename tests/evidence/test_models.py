from app.evidence.models import EvidenceItem, EvidenceSource, uuid4


def test_evidence_item_creation():
    item = EvidenceItem(
        source=EvidenceSource.THREAT_INTELLIGENCE,
        confidence=0.8,
        summary="test summary",
        raw_evidence={"url": "http://evil.com"},
        structured_evidence={"threat_status": "malicious"},
        supporting_artifacts=["art1", "art2"],
        metadata={"key": "val"},
    )
    assert item.evidence_id is not None
    assert item.source == EvidenceSource.THREAT_INTELLIGENCE
    assert item.confidence == 0.8
    assert item.summary == "test summary"
    assert item.raw_evidence == {"url": "http://evil.com"}
    assert item.structured_evidence == {"threat_status": "malicious"}
    assert item.supporting_artifacts == ["art1", "art2"]
    assert item.metadata == {"key": "val"}


def test_evidence_to_from_dict():
    item = EvidenceItem(
        source=EvidenceSource.LLM_REASONING,
        confidence=0.6,
        summary="llm thought",
    )
    d = item.to_dict()
    item2 = EvidenceItem.from_dict(d)
    assert item2.source == item.source
    assert item2.confidence == item.confidence
    assert item2.summary == item.summary
    assert item2.evidence_id == item.evidence_id


def test_evidence_defaults():
    item = EvidenceItem(source=EvidenceSource.CUSTOM)
    assert item.confidence == 0.5
    assert item.weight == 1.0
    assert item.summary == ""
    assert item.evidence_id is not None