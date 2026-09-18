"""Candidate generation foundation."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from .models import ResearchCandidate
from .enums import CandidateType, CandidateState, CandidateSource
from .repository import exists_by_key, create
from .config import config


def _make_id() -> str:
    return f"can-{uuid.uuid4().hex[:8]}"


def _deduplicate(candidate_type: CandidateType, source: CandidateSource, related_entity_id: Optional[str], related_ioc_id: Optional[str], related_actor_id: Optional[str] = None) -> bool:
    if not config.deduplication_enabled:
        return False
    existing = exists_by_key(candidate_type, source, related_entity_id, related_ioc_id, related_actor_id)
    return existing is not None


def create_candidate(
    candidate_type: CandidateType,
    title: str,
    description: str,
    source: CandidateSource,
    reason: str,
    research_scope: str = "general",
    priority: int = 5,
    urgency: int = 5,
    confidence: float = 0.5,
    evidence_count: int = 0,
    source_id: Optional[str] = None,
    related_analysis_id: Optional[str] = None,
    related_finding_id: Optional[str] = None,
    related_campaign_id: Optional[str] = None,
    related_entity_id: Optional[str] = None,
    related_ioc_id: Optional[str] = None,
    related_research_id: Optional[str] = None,
    related_actor_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[ResearchCandidate]:
    if not config.enabled or not config.candidates_enabled:
        return None

    if _deduplicate(candidate_type, source, related_entity_id, related_ioc_id, related_actor_id):
        return None

    now = datetime.utcnow()
    candidate = ResearchCandidate(
        candidate_id=_make_id(),
        candidate_type=candidate_type,
        title=title[:500],
        description=description[:2000],
        source=source,
        source_id=source_id,
        priority=max(1, min(10, priority)),
        urgency=max(1, min(10, urgency)),
        confidence=max(0.0, min(1.0, confidence)),
        evidence_count=max(0, evidence_count),
        first_seen=now,
        last_seen=now,
        status=CandidateState.NEW,
        research_scope=research_scope,
        related_analysis_id=related_analysis_id,
        related_finding_id=related_finding_id,
        related_campaign_id=related_campaign_id,
        related_entity_id=related_entity_id,
        related_ioc_id=related_ioc_id,
        related_research_id=related_research_id,
        related_actor_id=related_actor_id,
        reason=reason,
        created_at=now,
        updated_at=now,
        metadata=metadata or {}
    )
    create(candidate)
    return candidate


def generate_unknown_ioc(ioc_value: str, source: CandidateSource, source_id: Optional[str] = None) -> Optional[ResearchCandidate]:
    title = f"Unknown IOC: {ioc_value[:100]}"
    description = f"IOC {ioc_value} has no available threat intelligence."
    reason = "Threat intelligence is unavailable for a newly observed IOC."
    return create_candidate(
        candidate_type=CandidateType.UNKNOWN_IOC,
        title=title,
        description=description,
        source=source,
        reason=reason,
        research_scope="IOC reputation lookup",
        related_ioc_id=ioc_value,
        source_id=source_id,
        confidence=0.6
    )


def generate_new_infrastructure(infra_value: str, source: CandidateSource, source_id: Optional[str] = None) -> Optional[ResearchCandidate]:
    title = f"New infrastructure observed: {infra_value[:100]}"
    description = f"New infrastructure {infra_value} identified by existing subsystem."
    reason = "Infrastructure is newly observed and requires investigation."
    return create_candidate(
        candidate_type=CandidateType.NEW_INFRASTRUCTURE,
        title=title,
        description=description,
        source=source,
        reason=reason,
        research_scope="infrastructure relationship analysis",
        related_entity_id=infra_value,
        source_id=source_id,
        confidence=0.5
    )


def generate_attribution_hypothesis(hypothesis_id: str, description: str, source: CandidateSource = CandidateSource.ATTRIBUTION) -> Optional[ResearchCandidate]:
    title = f"Attribution hypothesis requires investigation"
    reason = "Attribution produced a hypothesis requiring further investigation."
    return create_candidate(
        candidate_type=CandidateType.ATTRIBUTION_HYPOTHESIS,
        title=title,
        description=description[:2000],
        source=source,
        reason=reason,
        research_scope="attribution hypothesis validation",
        related_actor_id=hypothesis_id,
        source_id=hypothesis_id,
        confidence=0.5
    )


def generate_contradiction(claim: str, source_a: str, source_b: str, source: CandidateSource = CandidateSource.SYSTEM) -> Optional[ResearchCandidate]:
    title = f"Contradictory intelligence: {claim[:100]}"
    description = f"Conflicting intelligence from {source_a} and {source_b} regarding claim: {claim}"
    reason = "Conflicting intelligence requires review."
    return create_candidate(
        candidate_type=CandidateType.CONTRADICTION,
        title=title,
        description=description[:2000],
        source=source,
        reason=reason,
        research_scope="source verification",
        confidence=0.6,
        related_entity_id=claim[:200]
    )


def generate_analyst_request(request_title: str, request_description: str, analyst_id: str) -> Optional[ResearchCandidate]:
    title = f"Analyst request: {request_title[:100]}"
    description = request_description[:2000]
    reason = "Analyst explicitly requested investigation."
    return create_candidate(
        candidate_type=CandidateType.ANALYST_REQUEST,
        title=title,
        description=description,
        source=CandidateSource.ANALYST,
        reason=reason,
        research_scope="general",
        source_id=analyst_id,
        confidence=0.8
    )
