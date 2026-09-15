"""Attribution API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from .attribution_engine import AttributionEngine

router = APIRouter(prefix="/api/v1/attribution")
engine = AttributionEngine()


class AnalyzeRequest(BaseModel):
    message_id: str
    text: str
    campaign_id: str | None = None


class AnalyzeResponse(BaseModel):
    message_id: str
    confidence: float
    actor_hypotheses: list
    infrastructure_count: int
    explanation: str


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    result = engine.analyze_message(req.message_id, req.text, req.campaign_id)
    return AnalyzeResponse(
        message_id=result.message_id,
        confidence=result.confidence,
        actor_hypotheses=[h.model_dump() for h in result.actor_hypotheses],
        infrastructure_count=len(result.infrastructure_links),
        explanation=result.explanation
    )


@router.get("/health")
def health():
    return {"status": "ok", "rfc": "RFC-014"}
