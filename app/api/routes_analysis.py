"""Route module: POST /api/analyze."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.analysis import AnalyzeRequest, AnalysisResult
from app.services.analysis_service import (
    ClassifierUnavailableError,
    analyze,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
def analyze_message(payload: AnalyzeRequest) -> dict:
    """Analyze a single message (SMS / text / email)."""
    try:
        return analyze(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ClassifierUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected analysis failure: %s", exc)
        raise HTTPException(status_code=500, detail="Internal analysis error") from exc