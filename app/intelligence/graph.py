"""Threat Graph integration for intelligence."""

from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel


class GraphLink(BaseModel):
    entity_id: str
    entity_type: str
    related_to: str
    confidence: float
    reason: str


def link_candidate_to_graph(candidate, graph_client=None) -> List[GraphLink]:
    links = []
    entity_id = getattr(candidate, "related_entity_id", None) or getattr(candidate, "related_ioc_id", None)
    if not entity_id:
        return links
    # Placeholder integration: in real system, query app.graph for entity
    links.append(GraphLink(
        entity_id=entity_id,
        entity_type="IOC",
        related_to=candidate.candidate_id,
        confidence=candidate.confidence,
        reason="Candidate linked from intelligence engine"
    ))
    return links


def enrich_candidate_with_graph(candidate, graph_client=None) -> Dict:
    enrichment = {
        "candidate_id": candidate.candidate_id,
        "graph_entities": [],
        "campaigns": [],
        "actors": []
    }
    entity_id = getattr(candidate, "related_entity_id", None)
    if entity_id:
        enrichment["graph_entities"].append({"id": entity_id, "type": "entity"})
    return enrichment


def query_graph_for_candidate(candidate_id: str, graph_client=None) -> Dict:
    # Stub: would query threat graph for related entities
    return {
        "candidate_id": candidate_id,
        "neighbors": [],
        "paths": []
    }
