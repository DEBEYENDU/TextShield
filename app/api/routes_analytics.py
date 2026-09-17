"""Analytics routes for TextShield."""

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.analytics.config import AnalyticsConfig
try:
    from analytics import get_metrics_engine, get_history, AuditService  # type: ignore
except ImportError:
    try:
        from app.analytics import get_metrics_engine, get_history  # type: ignore
        from app.analytics.audit import AuditService  # type: ignore
    except ImportError:
        get_metrics_engine = lambda: None  # type: ignore
        get_history = lambda: None  # type: ignore
        AuditService = object  # type: ignore

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/health", summary="Analytics system health check")
async def analytics_health():
    """Check analytics system health."""
    try:
        engine = get_metrics_engine()
        history = get_history()
        return {
            "status": "healthy",
            "total_records": len(engine.get_records()),
            "total_history_entries": len(history._records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Get metrics summary")
async def get_metrics_summary():
    """Get metrics summary."""
    try:
        engine = get_metrics_engine()
        records = engine.get_records()
        if not records:
            return {"message": "No metrics data available"}

        from analytics.statistics import StatisticsEngine

        stats = StatisticsEngine()

        return {
            "total_records": len(records),
            "confidence_distribution": stats.compute_confidence_distribution(records),
            "risk_distribution": stats.compute_risk_distribution(records),
            "common_intents": stats.compute_intent_frequencies(records),
            "common_behaviors": stats.compute_behavior_frequencies(records),
            "processing_time_stats": stats.compute_processing_time_stats(records),
            "daily_usage": stats.compute_daily_usage(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", summary="Get analysis history")
async def get_analysis_history(
    message_type: Optional[str] = None,
    classification: Optional[str] = None,
    risk_level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """Get analysis history with filtering and pagination."""
    try:
        history = get_history()
        from datetime import datetime

        records = history.get(
            message_type=message_type,
            classification=classification,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
        return {"records": records, "total": history.count()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history/clear", summary="Clear analysis history")
async def clear_history():
    """Clear all analysis history."""
    try:
        history = get_history()
        count = HistoryService.clear()
        return {"deleted_count": count, "message": "History cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history/prune", summary="Prune old history")
async def prune_history(days: int = 30):
    """Prune history older than specified days."""
    try:
        history = get_history()
        count = HistoryService.delete_older_than(days)
        return {"deleted_count": count, "message": "Old history pruned successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explainability", summary="Get explainability reports")
async def get_explainability_reports():
    """Get explainability reports."""
    try:
        from analytics.explainability import ExplainabilityEngine, ExplanationRecord
        from analytics.exporters import AnalyticsExporter

        engine = get_metrics_engine()
        records = engine.get_records()

        # Generate explanations for recent records
        explanations = []
        for record in engine.get_records()[:10]:  # Last 10 records
            try:
                explanation = ExplainabilityEngine.generate_explanation(record)
                explanations.append(explanation)
            except Exception:
                continue

        return {
            "total_explanations": len(explanations),
            "explanations": [
                {
                    "classification": e.classification,
                    "confidence": e.confidence,
                    "risk_level": e.risk_level,
                    "reasoning_summary": e.reasoning_summary,
                }
                for e in explanations
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/logs", summary="Get audit logs")
async def get_audit_logs(
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
):
    """Get audit logs."""
    try:
        audit_service = AuditService()
        events = AuditLogger().get_events(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return {"events": events, "total": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/log-event", summary="Log audit event")
async def log_event(event_type: str, event_data: Dict[str, Any]):
    """Log an audit event."""
    try:
        AuditService.log_event(event_type, event_data)
        return {"status": "logged", "event_type": event_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
