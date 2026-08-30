"""Analytics service: dashboard statistics."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.database.base import get_connection
from app.database.repositories import analytics_repository, history_repository

logger = get_logger(__name__)


def get_stats() -> dict[str, Any]:
    """Compute dashboard statistics (see ``StatsResponse``)."""
    with get_connection() as conn:
        totals = analytics_repository.totals(conn)
        daily = analytics_repository.per_day(conn, days=14)
        latest = history_repository.latest_timestamp(conn)
    return {
        "total_analyses": totals["total"],
        "spam_count": totals["spam"],
        "ham_count": totals["ham"],
        "spam_percentage": (
            round(totals["spam"] / totals["total"] * 100, 1) if totals["total"] else 0.0
        ),
        "average_confidence": totals["average_confidence"],
        "risk_distribution": totals["risk_distribution"],
        "message_type_distribution": totals["message_type_distribution"],
        "intent_distribution": totals["intent_distribution"],
        "analyses_per_day": daily,
        "latest_analysis_at": latest,
    }
