"""Tests for contradiction and provenance."""

from app.intelligence.contradiction import detect_contradiction, resolve_contradiction, list_unresolved, ContradictionSeverity
from app.intelligence.provenance import create_provenance, add_lineage, verify_chain


def test_detect_contradiction():
    rec = detect_contradiction("domain", "srcA", "malicious", 0.8, "srcB", "benign", 0.7)
    assert rec is not None
    assert rec.claim == "domain"
    assert rec.severity in (ContradictionSeverity.MEDIUM, ContradictionSeverity.HIGH)


def test_no_contradiction():
    rec = detect_contradiction("domain", "srcA", "malicious", 0.8, "srcB", "malicious", 0.7)
    assert rec is None


def test_resolve_contradiction():
    rec = detect_contradiction("x", "a", "1", 0.5, "b", "2", 0.5)
    rec = resolve_contradiction(rec, "Manual review resolved")
    assert rec.resolved is True
    assert rec.resolution_notes == "Manual review resolved"


def test_list_unresolved():
    r1 = detect_contradiction("x", "a", "1", 0.5, "b", "2", 0.5)
    r2 = detect_contradiction("y", "a", "1", 0.5, "b", "2", 0.5)
    r2.resolved = True
    unresolved = list_unresolved([r1, r2])
    assert len(unresolved) == 1


def test_provenance_create():
    p = create_provenance(entity_id="e1", source_id="s1", source_type="threat_intel", evidence_hash="abc123")
    assert p.entity_id == "e1"
    assert p.evidence_hash == "abc123"


def test_provenance_lineage():
    p = create_provenance(entity_id="e1", source_id="s1", source_type="t", evidence_hash="h")
    add_lineage(p, "parent1")
    add_lineage(p, "parent2")
    assert "parent1" in p.lineage
    assert len(p.lineage) == 2


def test_verify_chain():
    p1 = create_provenance("e1", "s1", "t", "h")
    p2 = create_provenance("e2", "", "t", "h")
    assert verify_chain([p1]) is True
    assert verify_chain([p2]) is False
