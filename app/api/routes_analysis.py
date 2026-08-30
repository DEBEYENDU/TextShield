"""Route module: POST /api/analyze (thin wrapper over the service)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.container import ServiceRegistry, get_request_registry
from app.core.exceptions import AppError, ServiceUnavailableError, ValidationAppError
from app.core.logging import get_logger
from app.schemas.analysis import AnalyzeRequest, AnalysisResult

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResult)
def analyze_message(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Analyze a single message (SMS / text / email)."""
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
