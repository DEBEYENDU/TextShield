"""Tests for RAG governance integration."""

from app.intelligence.rag import RagDocument, RagGovernancePolicy, filter_documents_for_rag, promote_to_rag, audit_rag_integration
from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate


def make_candidate(confidence=0.5):
    return ResearchCandidate(
        candidate_id="can-1",
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        confidence=confidence,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_filter_documents():
    docs = [
        RagDocument(doc_id="1", content="a", source="s", confidence=0.8, provenance="p"),
        RagDocument(doc_id="2", content="b", source="s", confidence=0.5, provenance="p"),
        RagDocument(doc_id="3", content="c", source="s", confidence=0.9, provenance=""),
    ]
    policy = RagGovernancePolicy(min_confidence=0.7, require_provenance=True)
    filtered = filter_documents_for_rag(docs, policy)
    assert len(filtered) == 1
    assert filtered[0].doc_id == "1"


def test_promote_to_rag():
    docs = [RagDocument(doc_id="1", content="a", source="s", confidence=0.8, provenance="p")]
    policy = RagGovernancePolicy(allow_promotion=True, min_confidence=0.7)
    result = promote_to_rag(make_candidate(), docs, policy)
    assert len(result) == 1


def test_promote_disabled():
    docs = [RagDocument(doc_id="1", content="a", source="s", confidence=0.9, provenance="p")]
    policy = RagGovernancePolicy(allow_promotion=False)
    result = promote_to_rag(make_candidate(), docs, policy)
    assert len(result) == 0


def test_audit_rag_integration():
    c1 = make_candidate(confidence=0.8)
    c2 = make_candidate(confidence=0.4)
    audit = audit_rag_integration([c1, c2])
    assert audit["promoted"] == 1
    assert audit["rejected"] == 1
    assert audit["total_candidates"] == 2
