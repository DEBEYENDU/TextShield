"""Response API."""

from fastapi import APIRouter
from pydantic import BaseModel
from .decision import ResponseDecider
from .models import PolicyType

router = APIRouter(prefix="/api/v1/response")
decider = ResponseDecider()


class EvaluateRequest(BaseModel):
    analysis_id: str
    decision_id: str
    classification: str
    risk_level: str
    confidence: float
    policy: str = "CONSERVATIVE"
    attribution_confidence: float = 0.0


class EvaluateResponse(BaseModel):
    response_id: str
    action: str
    confidence: float
    requires_approval: bool
    reason: str


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest):
    policy = PolicyType(req.policy.upper())
    decision = decider.decide(
        req.analysis_id, req.decision_id, req.classification,
        req.risk_level, req.confidence, policy, req.attribution_confidence
    )
    return EvaluateResponse(
        response_id=decision.response_id,
        action=decision.action.value,
        confidence=decision.confidence,
        requires_approval=decision.requires_approval,
        reason=decision.reason
    )


@router.get("/health")
def health():
    return {"status": "ok", "rfc": "RFC-015"}
