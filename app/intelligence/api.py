"""Intelligence API endpoints."""

from __future__ import annotations
from typing import List
from fastapi import APIRouter
from .models import ResearchCandidate
from .enums import CandidateState
from .repository import list_all
from .prioritization import prioritize_many
from .gaps import detect_gaps_from_candidates
from .coverage import calculate_coverage, overall_coverage

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


@router.get("/candidates")
def get_candidates(status: str | None = None, limit: int = 100):
    state = CandidateState(status) if status else None
    candidates = list_all(status=state, limit=limit)
    return [c.model_dump() for c in candidates]


@router.get("/candidates/{candidate_id}/priority")
def get_candidate_priority(candidate_id: str):
    from .repository import get
    candidate = get(candidate_id)
    if not candidate:
        return {"error": "not found"}
    result = prioritize_many([candidate])[0]
    return result.model_dump() if hasattr(result, "model_dump") else result.__dict__


@router.get("/gaps")
def get_gaps():
    candidates = list_all(limit=500)
    gaps = detect_gaps_from_candidates(candidates)
    return [g.model_dump() for g in gaps]


@router.get("/coverage")
def get_coverage():
    candidates = list_all(limit=500)
    gaps = detect_gaps_from_candidates(candidates)
    metrics = calculate_coverage(candidates, gaps)
    overall = overall_coverage(metrics)
    return {
        "overall": overall,
        "domains": {d.value: m.model_dump() for d, m in metrics.items()}
    }
