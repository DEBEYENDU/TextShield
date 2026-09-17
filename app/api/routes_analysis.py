"""Route module: POST /api/analyze + POST /api/analysis (thin wrappers)."""

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


@router.post("/analysis")
def multi_agent_analysis(
    payload: AnalyzeRequest,
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Multi-agent security reasoning: full analysis + agent reports,
    consensus, fused evidence, confidence, trust/threat and entities."""
    from app.agents.orchestrator import AgentOrchestrator

    analyze = registry.get("analysis")
    try:
        result = analyze(payload)
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
    try:
        text = payload.message or payload.body or payload.email_raw or ""
        orchestrator = AgentOrchestrator()
        ctx = orchestrator.build_context(
            result, text=text, sender=payload.sender or "",
            subject=payload.subject or "")
        report = orchestrator.run(ctx)
    except Exception as exc:
        logger.exception("Multi-agent reasoning failed: %s", exc)
        raise AppError("Multi-agent reasoning failed") from exc
    return {
        "classification": result.get("classification"),
        "confidence": result.get("confidence"),
        "risk_level": result.get("risk_level"),
        "risk_score": result.get("risk_score"),
        "agent_reports": report.get("agent_reports", []),
        "agents": report.get("agents", []),
        "consensus": report.get("consensus"),
        "overall_risk": report.get("overall_risk"),
        "evidence": report.get("evidence", {}),
        "trust_score": report.get("trust_score"),
        "threat_score": report.get("threat_score"),
        "entities": report.get("entities", {}),
        "knowledge": report.get("knowledge", {}),
        "conflicts": report.get("conflicts", []),
        "summary": report.get("summary", ""),
        "recommendation": report.get("recommendation", ""),
    }
