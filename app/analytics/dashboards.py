from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta


def get_dashboard_summary() -> Dict[str, Any]:
    """Return overall dashboard summary statistics.

    In a production deployment this would query the database/cache.
    """
    return {
        "total_analyses": 1247,
        "threat_score_distribution": {
            "low": 520,
            "medium": 410,
            "high": 210,
            "critical": 107,
        },
        "average_confidence": 0.73,
        "high_risk_detections": 317,
        "provider_health": {
            "google_safe_browsing": {"status": "healthy", "latency_ms": 120},
            "virustotal": {"status": "healthy", "latency_ms": 210},
            "openphish": {"status": "degraded", "latency_ms": 300},
        },
    }


def get_provider_status() -> Dict[str, Any]:
    """Return per‑provider health & quota stats."""
    return {
        "google_safe_browsing": {
            "health": "healthy",
            "latency_ms": 115,
            "success_rate": 0.99,
            "failure_rate": 0.01,
            "quota_used": 847,
            "quota_total": 1000,
            "circuit_breaker": "closed",
        },
        "virustotal": {
            "health": "healthy",
            "latency_ms": 210,
            "success_rate": 0.97,
            "failure_rate": 0.03,
            "quota_used": 1203,
            "quota_total": 2500,
            "circuit_breaker": "closed",
        },
        "openphish": {
            "health": "degraded",
            "latency_ms": 340,
            "success_rate": 0.85,
            "failure_rate": 0.15,
            "quota_used": 400,
            "quota_total": 500,
            "circuit_breaker": "open",
        },
    }


def get_threat_history(
    page: int = 1,
    page_size: int = 50,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    ioc_type: Optional[str] = None,
    provider: Optional[str] = None,
    severity: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a searchable, paginated threat history list."""
    base = datetime.now(timezone.utc)
    entries = []
    for i in range(200):
        entries.append(
            {
                "id": i,
                "ioc_value": f"http://example{i % 50}.com",
                "ioc_type": ["url", "domain", "ip", "email", "hash"][i % 5],
                "threat_score": round(0.1 + (i % 20) * 0.04, 2),
                "provider": ["google_safe_browsing", "virustotal", "openphish", "phishtank", "urlhaus"][i % 5],
                "severity": ["Low", "Medium", "High", "Critical"][i % 4],
                "timestamp": (base - timedelta(hours=i * 2)).isoformat(),
            }
        )

    filtered = entries
    if ioc_type:
        filtered = [e for e in filtered if e["ioc_type"] == ioc_type]
    if provider:
        filtered = [e for e in filtered if e["provider"] == provider]
    if severity:
        filtered = [e for e in filtered if e["severity"] == severity]

    total = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_entries = filtered[start_idx:end_idx]

    return {
        "entries": page_entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def get_cache_statistics() -> Dict[str, Any]:
    """Return cache analytics."""
    return {
        "cache_size": 3842,
        "hit_ratio": 0.86,
        "miss_ratio": 0.14,
        "ttl_distribution": {
            "< 1h": 45,
            "1h - 6h": 30,
            "6h - 24h": 15,
            "> 24h": 10,
        },
        "evictions": 127,
        "top_queried_iocs": [
            {"value": "http://example1.com", "count": 87},
            {"value": "http://example2.com", "count": 63},
            {"value": "http://example3.com", "count": 55},
        ],
    }


def get_execution_metrics() -> Dict[str, Any]:
    """Return execution pipeline metrics."""
    return {
        "average_lookup_time_ms": 87,
        "concurrency": 12,
        "queue_depth": 5,
        "retries_total": 342,
        "timeouts": 12,
        "requests_per_second": 890,
    }


def get_confidence_breakdown() -> Dict[str, Any]:
    """Break down confidence contribution by source."""
    return {
        "threat_intelligence": 0.38,
        "hybrid_ml": 0.22,
        "llm_reasoning": 0.15,
        "rules": 0.12,
        "rag_retrieval": 0.08,
        "semantic_analysis": 0.05,
        "intent_analysis": 0.05,
    }