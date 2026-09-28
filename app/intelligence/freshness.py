"""Knowledge freshness engine."""

from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"


class KnowledgeFreshnessRecord(BaseModel):
    freshness_id: str = Field(default_factory=lambda: f"frsh-{uuid.uuid4().hex[:8]}")
    entity_id: Optional[str] = None
    candidate_id: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None
    age_days: float = 0.0
    staleness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    status: FreshnessStatus = FreshnessStatus.FRESH
    metadata: dict = Field(default_factory=dict)


def _age_days(last_seen: datetime, now: Optional[datetime] = None) -> float:
    now = now or datetime.utcnow()
    delta = now - last_seen
    return max(0.0, delta.total_seconds() / 86400.0)


def compute_staleness(age_days: float, half_life: float = 30.0) -> float:
    if age_days <= 0:
        return 1.0
    import math
    score = math.exp(-age_days / half_life)
    return max(0.0, min(1.0, score))


def classify_freshness(staleness_score: float) -> FreshnessStatus:
    if staleness_score >= 0.7:
        return FreshnessStatus.FRESH
    if staleness_score >= 0.3:
        return FreshnessStatus.STALE
    return FreshnessStatus.EXPIRED


def evaluate_candidate_freshness(candidate, now: Optional[datetime] = None, half_life: float = 30.0) -> KnowledgeFreshnessRecord:
    now = now or datetime.utcnow()
    last_seen = candidate.last_seen or candidate.created_at or now
    age = _age_days(last_seen, now)
    score = compute_staleness(age, half_life)
    status = classify_freshness(score)
    return KnowledgeFreshnessRecord(
        entity_id=candidate.related_entity_id or candidate.related_ioc_id,
        candidate_id=candidate.candidate_id,
        last_seen=last_seen,
        age_days=round(age, 2),
        staleness_score=round(score, 3),
        status=status,
        metadata={"candidate_type": str(candidate.candidate_type)}
    )


def detect_stale_candidates(candidates: List, max_age_days: float = 90.0, half_life: float = 30.0) -> List[KnowledgeFreshnessRecord]:
    records = []
    for c in candidates:
        rec = evaluate_candidate_freshness(c, half_life=half_life)
        if rec.age_days > max_age_days or rec.status in (FreshnessStatus.STALE, FreshnessStatus.EXPIRED):
            records.append(rec)
    return records


def needs_refresh(record: KnowledgeFreshnessRecord, refresh_threshold: float = 0.5) -> bool:
    return record.staleness_score < refresh_threshold or record.status == FreshnessStatus.EXPIRED
