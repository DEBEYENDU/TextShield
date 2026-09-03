from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.analytics.dashboards import (
    get_dashboard_summary,
    get_provider_status,
    get_threat_history,
    get_cache_statistics,
    get_execution_metrics,
    get_confidence_breakdown,
)
from app.analytics.history import get_dashboard_history, get_severity_distribution
from app.analytics.summaries import get_threat_score_distribution, get_provider_comparison

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 50


class HistoryFilters(BaseModel):
    ioc_type: Optional[str] = None
    provider: Optional[str] = None
    severity: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("/summary")
def dashboard_summary():
    return get_dashboard_summary()


@router.get("/providers")
def dashboard_providers():
    return get_provider_status()


@router.get("/history")
def dashboard_history(filters: HistoryFilters = Pagination()):
    try:
        hist = get_dashboard_history(
            page=filters.page,
            page_size=filters.page_size,
            ioc_type=filters.ioc_type,
            provider=filters.provider,
            severity=filters.severity,
        )
        return hist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache")
def dashboard_cache():
    from app.analytics.dashboards import get_cache_statistics
    return get_cache_statistics()


@router.get("/metrics")
def dashboard_metrics():
    from app.analytics.dashboards import get_execution_metrics
    return get_execution_metrics()


@router.get("/threats")
def dashboard_threats():
    hist = get_dashboard_history(page=1, page_size=10)
    return {"recent_threats": hist["entries"]}


@router.get("/score-distribution")
def score_distribution():
    from app.analytics.summaries import get_threat_score_distribution
    return get_threat_score_distribution()


@router.get("/provider-comparison/{ioc_value}")
def provider_comparison(ioc_value: str):
    from app.analytics.summaries import get_provider_comparison
    return get_provider_comparison(ioc_value)


@router.get("/history/filters")
def history_filters():
    return {
        "ioc_types": ["url", "domain", "ip", "email", "hash"],
        "providers": ["google_safe_browsing", "virustotal", "openphish", "phishtank", "urlhaus"],
        "severities": ["Low", "Medium", "High", "Critical"],
    }