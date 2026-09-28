"""Knowledge gap detection engine."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class GapType(str, Enum):
    MISSING_CONTEXT = "MISSING_CONTEXT"
    MISSING_IOC = "MISSING_IOC"
    MISSING_CAMPAIGN_LINK = "MISSING_CAMPAIGN_LINK"
    MISSING_ATTRIBUTION = "MISSING_ATTRIBUTION"
    UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
    COVERAGE_LOW = "COVERAGE_LOW"


class KnowledgeGap(BaseModel):
    gap_id: str = Field(default_factory=lambda: f"gap-{uuid.uuid4().hex[:8]}")
    gap_type: GapType
    entity_id: Optional[str] = None
    description: str
    severity: int = Field(default=5, ge=1, le=10)
    coverage_score: float = Field(default=0.5, ge=0.0, le=1.0)
    first_detected: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


def _make_gap(gap_type: GapType, description: str, entity_id: Optional[str] = None, severity: int = 5, coverage_score: float = 0.5) -> KnowledgeGap:
    return KnowledgeGap(
        gap_type=gap_type,
        entity_id=entity_id,
        description=description,
        severity=max(1, min(10, severity)),
        coverage_score=max(0.0, min(1.0, coverage_score))
    )


def detect_missing_context(candidate) -> Optional[KnowledgeGap]:
    if not candidate.description or len(candidate.description.strip()) < 20:
        return _make_gap(
            GapType.MISSING_CONTEXT,
            f"Candidate {candidate.candidate_id} has insufficient context.",
            entity_id=candidate.related_entity_id or candidate.related_ioc_id,
            severity=4,
            coverage_score=0.3
        )
    return None


def detect_missing_ioc(candidate) -> Optional[KnowledgeGap]:
    if candidate.candidate_type.value == "UNKNOWN_IOC" and not candidate.related_ioc_id:
        return _make_gap(
            GapType.MISSING_IOC,
            f"Unknown IOC candidate {candidate.candidate_id} lacks IOC identifier.",
            entity_id=candidate.candidate_id,
            severity=7,
            coverage_score=0.2
        )
    return None


def detect_missing_attribution(candidate) -> Optional[KnowledgeGap]:
    if candidate.candidate_type.value == "ATTRIBUTION_HYPOTHESIS" and not candidate.related_actor_id:
        return _make_gap(
            GapType.MISSING_ATTRIBUTION,
            f"Attribution hypothesis candidate {candidate.candidate_id} lacks actor link.",
            entity_id=candidate.candidate_id,
            severity=6,
            coverage_score=0.4
        )
    return None


def detect_gaps_from_candidates(candidates: List) -> List[KnowledgeGap]:
    gaps: List[KnowledgeGap] = []
    seen = set()
    for c in candidates:
        for detector in (detect_missing_context, detect_missing_ioc, detect_missing_attribution):
            gap = detector(c)
            if gap:
                key = (gap.gap_type, gap.entity_id)
                if key not in seen:
                    gaps.append(gap)
                    seen.add(key)
    return gaps
