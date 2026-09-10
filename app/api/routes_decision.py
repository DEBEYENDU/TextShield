"""Dashboard API: adaptive decisions, evidence, confidence and review."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.container import ServiceRegistry, get_request_registry
from app.core.exceptions import AppError, ServiceUnavailableError, ValidationAppError
from app.core.logging import get_logger
from app.schemas.analysis import AnalyzeRequest
from fastapi import Depends

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["decision"])


class ReviewResolveIn(BaseModel):
    verdict: str
    analyst: str = "dashboard"
    comment: str = ""


def _analyze(payload: AnalyzeRequest, registry: ServiceRegistry) -> dict:
    analyze = registry.get("analysis")
    try:
        return analyze(payload)
    except ValidationAppError as exc:
        raise exc
    except ServiceUnavailableError as exc:
        raise exc
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Unexpected analysis failure: %s", exc)
        raise AppError("Internal analysis error") from exc


def _decision_block(result: dict) -> dict:
    decision = result.get("adaptive_decision", {}) or {}
    if not decision:
        raise AppError("Adaptive decision unavailable")
    return decision


@router.post("/decision")
def adaptive_decision(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Final adaptive decision with confidence, evidence, policy and review."""
    result = _analyze(payload, registry)
    decision = _decision_block(result)
    return {
        "decision": decision.get("decision"),
        "p_spam": decision.get("p_spam"),
        "confidence": decision.get("confidence"),
        "risk": decision.get("risk"),
        "policy": decision.get("policy"),
        "category": decision.get("category"),
        "evidence_summary": decision.get("explanation", {}),
        "review": decision.get("review", {}),
        "classification": result.get("classification"),
        "risk_level": result.get("risk_level"),
    }


@router.post("/evidence")
def evidence_summary(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Per-source evidence, adaptive weights and capped shares."""
    result = _analyze(payload, registry)
    decision = _decision_block(result)
    return {
        "sources": decision.get("sources", {}),
        "weights": decision.get("weights", {}),
        "shares": decision.get("shares", {}),
        "contributions": decision.get("contributions", []),
        "n_sources": decision.get("n_sources", 0),
        "policy": decision.get("policy"),
        "category": decision.get("category"),
    }


@router.post("/confidence")
def confidence_breakdown(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Context-aware confidence: agreement, coverage and calibration."""
    result = _analyze(payload, registry)
    decision = _decision_block(result)
    return {
        "confidence": decision.get("confidence"),
        "raw_confidence": decision.get("raw_confidence"),
        "agreement": decision.get("agreement"),
        "coverage": decision.get("coverage"),
        "uncertainty": decision.get("uncertainty"),
        "policy": decision.get("policy"),
    }


@router.post("/review")
def review_route(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Route a message for human review; returns routing + queue status."""
    from app.decision.review import review_queue

    result = _analyze(payload, registry)
    decision = _decision_block(result)
    routing = decision.get("review", {})
    return {"routing": routing, "queue": review_queue.stats(),
            "decision": decision.get("decision"),
            "risk": decision.get("risk")}


@router.get("/review")
def review_queue_list(limit: int = 50) -> dict:
    """List pending human reviews."""
    from app.decision.review import review_queue

    return {"queue": review_queue.queue(limit=limit),
            "stats": review_queue.stats()}


@router.post("/review/{feedback_id}/claim")
def review_claim(feedback_id: str, analyst: str = "dashboard") -> dict:
    from app.decision.review import review_queue

    return {"claimed": review_queue.claim(feedback_id, analyst)}


@router.post("/review/{feedback_id}/resolve")
def review_resolve(feedback_id: str, payload: ReviewResolveIn) -> dict:
    from app.decision.review import review_queue

    try:
        resolved = review_queue.resolve(feedback_id, payload.verdict,
                                        payload.analyst, payload.comment)
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc
    return {"resolved": resolved}


@router.get("/decision/policies")
def decision_policies() -> dict:
    """List available decision policies and the active default."""
    from app.decision.policy import POLICY_NAMES, load_policies

    bundle = load_policies()
    return {"active": os.getenv("DECISION_POLICY", "balanced"),
            "policies": {name: bundle["policies"][name].to_dict()
                         for name in POLICY_NAMES if name in bundle["policies"]}}
