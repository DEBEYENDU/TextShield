"""Intelligence candidate prioritization engine.

Deterministic, explainable prioritization for research candidates.
Priority is research value/urgency, NOT threat risk or maliciousness.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from .models import ResearchCandidate
from .enums import CandidateType, CandidateState
from .config import config


class PriorityFactor(BaseModel):
    name: str
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)
    reason: str


class CandidatePriority(BaseModel):
    candidate_id: str
    priority_score: float = Field(ge=0.0, le=1.0)
    priority_level: str
    factors: List[PriorityFactor]
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_summary: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


_PRIORITY_BANDS = [
    (0.75, "CRITICAL"),
    (0.5, "HIGH"),
    (0.25, "MEDIUM"),
    (0.0, "LOW"),
]


def _normalize(value: float, min_v: float, max_v: float) -> float:
    if value < min_v:
        value = min_v
    if value > max_v:
        value = max_v
    return (value - min_v) / (max_v - min_v) if max_v > min_v else 0.5


def _age_days(candidate: ResearchCandidate) -> float:
    now = datetime.utcnow()
    try:
        age = (now - candidate.first_seen).total_seconds() / 86400
    except Exception:
        age = 0.0
    return max(0.0, age)


def _compute_factors(candidate: ResearchCandidate) -> List[PriorityFactor]:
    factors: List[PriorityFactor] = []

    # Evidence gap: low evidence_count -> higher priority
    evidence_count_norm = _normalize(candidate.evidence_count, 0, 10)
    evidence_gap = 1.0 - evidence_count_norm
    factors.append(PriorityFactor(
        name="evidence_gap",
        value=round(evidence_gap, 3),
        weight=0.20,
        contribution=round(evidence_gap * 0.20, 3),
        reason=f"Evidence count is {candidate.evidence_count}"
    ))

    # Uncertainty: low confidence -> higher priority
    uncertainty = 1.0 - max(0.0, min(1.0, candidate.confidence))
    factors.append(PriorityFactor(
        name="uncertainty",
        value=round(uncertainty, 3),
        weight=0.20,
        contribution=round(uncertainty * 0.20, 3),
        reason=f"Candidate confidence is {candidate.confidence:.2f}"
    ))

    # Novelty: recent first_seen -> higher novelty
    age = _age_days(candidate)
    # Normalize age 0-365 days to novelty
    novelty = 1.0 - _normalize(age, 0, 365)
    factors.append(PriorityFactor(
        name="novelty",
        value=round(novelty, 3),
        weight=0.15,
        contribution=round(novelty * 0.15, 3),
        reason=f"Age {age:.1f} days"
    ))

    # Recurrence: evidence_count proxy
    recurrence = _normalize(candidate.evidence_count, 0, 20)
    factors.append(PriorityFactor(
        name="recurrence",
        value=round(recurrence, 3),
        weight=0.10,
        contribution=round(recurrence * 0.10, 3),
        reason=f"Evidence count {candidate.evidence_count}"
    ))

    # Operational impact: urgency field
    urgency_norm = _normalize(candidate.urgency, 1, 10)
    factors.append(PriorityFactor(
        name="operational_impact",
        value=round(urgency_norm, 3),
        weight=0.15,
        contribution=round(urgency_norm * 0.15, 3),
        reason=f"Urgency {candidate.urgency}"
    ))

    # Research value: candidate_type specific weight
    type_weights = {
        CandidateType.UNKNOWN_IOC: 0.8,
        CandidateType.CONTRADICTION: 0.9,
        CandidateType.ATTRIBUTION_HYPOTHESIS: 0.85,
        CandidateType.NEW_INFRASTRUCTURE: 0.7,
        CandidateType.CAMPAIGN_CORRELATION: 0.8,
        CandidateType.THREAT_INTEL_GAP: 0.75,
        CandidateType.REPEATED_PATTERN: 0.6,
        CandidateType.ANALYST_REQUEST: 0.9,
        CandidateType.MODEL_UNCERTAINTY: 0.7,
    }
    type_value = type_weights.get(candidate.candidate_type, 0.5)
    factors.append(PriorityFactor(
        name="research_value",
        value=round(type_value, 3),
        weight=0.15,
        contribution=round(type_value * 0.15, 3),
        reason=f"Candidate type {candidate.candidate_type.value}"
    ))

    # Research cost penalty: higher cost reduces priority
    cost_map = {
        CandidateType.UNKNOWN_IOC: 0.3,
        CandidateType.CONTRADICTION: 0.5,
        CandidateType.ATTRIBUTION_HYPOTHESIS: 0.6,
        CandidateType.NEW_INFRASTRUCTURE: 0.4,
        CandidateType.CAMPAIGN_CORRELATION: 0.5,
        CandidateType.ANALYST_REQUEST: 0.2,
    }
    cost = cost_map.get(candidate.candidate_type, 0.4)
    cost_factor = 1.0 - cost
    factors.append(PriorityFactor(
        name="research_cost_adjustment",
        value=round(cost_factor, 3),
        weight=0.05,
        contribution=round(cost_factor * 0.05, 3),
        reason=f"Estimated cost {cost:.2f}"
    ))

    return factors


def _band_for_score(score: float) -> str:
    for threshold, band in _PRIORITY_BANDS:
        if score >= threshold:
            return band
    return "LOW"


def prioritize(candidate: ResearchCandidate) -> CandidatePriority:
    if not config.enabled:
        score = 0.0
    else:
        factors = _compute_factors(candidate)
        total = sum(f.contribution for f in factors)
        # Clamp
        score = max(0.0, min(1.0, total))

    band = _band_for_score(score)
    factors = _compute_factors(candidate)
    reasons = [f"{f.name}: {f.reason} (value={f.value:.2f})" for f in factors]
    explanation = f"Candidate {candidate.candidate_id} prioritized as {band} due to: {'; '.join(reasons)}"

    evidence_summary = (
        f"Type={candidate.candidate_type.value}, "
        f"Evidence count={candidate.evidence_count}, "
        f"Confidence={candidate.confidence:.2f}, "
        f"Urgency={candidate.urgency}"
    )

    # Overall confidence in prioritization is based on candidate confidence and evidence
    conf = max(0.0, min(1.0, (candidate.confidence + _normalize(candidate.evidence_count, 0, 10)) / 2))

    return CandidatePriority(
        candidate_id=candidate.candidate_id,
        priority_score=round(score, 3),
        priority_level=band,
        factors=factors,
        explanation=explanation,
        confidence=round(conf, 3),
        evidence_summary=evidence_summary,
        generated_at=datetime.utcnow()
    )


def prioritize_many(candidates: List[ResearchCandidate]) -> List[CandidatePriority]:
    return [prioritize(c) for c in candidates]
