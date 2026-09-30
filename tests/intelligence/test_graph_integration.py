"""Tests for threat graph integration."""

from app.intelligence.enums import CandidateType, CandidateSource, CandidateState
from app.intelligence.models import ResearchCandidate
from app.intelligence.graph import link_candidate_to_graph, enrich_candidate_with_graph, query_graph_for_candidate


def make_candidate(entity_id="e1"):
    return ResearchCandidate(
        candidate_id="can-1",
        candidate_type=CandidateType.UNKNOWN_IOC,
        title="Test",
        description="Desc",
        source=CandidateSource.HUNTING,
        related_entity_id=entity_id,
        confidence=0.7,
        status=CandidateState.NEW,
        reason="Test"
    )


def test_link_candidate():
    c = make_candidate()
    links = link_candidate_to_graph(c)
    assert len(links) == 1
    assert links[0].entity_id == "e1"
    assert links[0].related_to == "can-1"


def test_link_no_entity():
    c = make_candidate(entity_id=None)
    links = link_candidate_to_graph(c)
    assert len(links) == 0


def test_enrich_candidate():
    c = make_candidate()
    data = enrich_candidate_with_graph(c)
    assert data["candidate_id"] == "can-1"
    assert len(data["graph_entities"]) == 1


def test_query_graph():
    result = query_graph_for_candidate("can-1")
    assert result["candidate_id"] == "can-1"
    assert "neighbors" in result
