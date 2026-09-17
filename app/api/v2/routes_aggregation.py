from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.threat.aggregation import (
    AggregationEngine, ThreatProfile, EvidenceFuser,
    WeightedScorer, ConfidenceCalculator, ConflictDetector,
)

router = APIRouter(prefix="/threat", tags=["threat-aggregation"])

# Global aggregation engine instance
_engine: Optional[AggregationEngine] = None


def get_engine() -> AggregationEngine:
    global _engine
    if _engine is None:
        _engine = AggregationEngine(
            weights=WeightedScorer(),
            calculator=ConfidenceCalculator(),
            conflict_detector=ConflictDetector(),
        )
    return _engine


class AggregateRequest(BaseModel):
    evidences: List[Dict[str, Any]]
    provider_names: Optional[List[str]] = None
    provider_reliability: Optional[Dict[str, float]] = None
    provider_timestamps: Optional[Dict[str, float]] = None


@router.post("/aggregate")
def aggregate_threat_profile(req: AggregateRequest):
    try:
        engine = get_engine()
        profile = engine.aggregate(
            evidences=req.evidences,
            provider_names=req.provider_names,
            provider_reliability=req.provider_reliability,
            provider_timestamps=req.provider_timestamps,
        )
        return profile.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProfileRequest(BaseModel):
    ioc_value: str
    ioc_type: str = "url"


@router.get("/profile/{ioc_value}")
def get_threat_profile(ioc_value: str, ioc_type: str = "url"):
    # In a full implementation, this would look up the IOC in the cache
    # and return any aggregated profile that exists.
    # For now return a default/profile-not-found response.
    return {
        "ioc_value": ioc_value,
        "ioc_type": ioc_type,
        "profile": None,
        "message": "Profile not found - run aggregation first",
    }