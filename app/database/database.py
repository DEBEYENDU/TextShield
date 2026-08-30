"""Persistence facade (V2.0 migration layer).

History of the module:

* V1: the single SQLite access point for analysis history (schema
  defined inline, ad-hoc SQL in every function).
* V2.0: schema definition moved to migrations (``app/database/
  migrations.py``), connection handling to ``app/database/base.py`` and
  row access to the repository package. This module stays as a thin
  facade so existing callers keep working unchanged.

New code should depend on ``app.database.base`` + ``app.database.
repositories`` directly instead of this module.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.database.base import get_connection, get_db_path, init_db
from app.database.repositories import (
    analytics_repository,
    history_repository,
)

logger = get_logger(__name__)


def insert_analysis(record: dict) -> int:
    """Insert one history record; returns the new row id."""
    init_db()
    with get_connection() as conn:
        return history_repository.create(conn, record)


def query_history(
    filters: dict | None = None,
    limit: int = 50,
    offset: int = 0,
    order_by: str = "timestamp",
    direction: str = "desc",
) -> list[dict]:
    """Query history with optional filters and ordering.

    Returns ``(rows, total_count)`` — the V1 call convention.
    """
    init_db()
    filters = filters or {}
    allowed_columns = {
        "timestamp",
        "input_type",
        "classification",
        "risk_level",
        "confidence",
        "id",
    }
    if order_by not in allowed_columns:
        order_by = "timestamp"
    direction = "asc" if direction.lower() == "asc" else "desc"

    conditions, params = [], []
    for column in ("input_type", "classification", "risk_level"):
        if filters.get(column):
            conditions.append(f"{column} = ?")
            params.append(filters[column])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM analyses {where} "
            f"ORDER BY {order_by} {direction} LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        total = int(
            conn.execute(
                f"SELECT COUNT(*) AS c FROM analyses {where}", params
            ).fetchone()["c"]
        )
    return [dict(row) for row in rows], total


def delete_history_entry(entry_id: int) -> bool:
    init_db()
    with get_connection() as conn:
        return history_repository.delete_by_id(conn, entry_id)


def clear_history() -> int:
    init_db()
    with get_connection() as conn:
        return history_repository.clear(conn)


def aggregate_stats() -> dict:
    """Compute dashboard statistics from the history table."""
    init_db()
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


__all__ = [
    "get_connection",
    "get_db_path",
    "init_db",
    "insert_analysis",
    "query_history",
    "delete_history_entry",
    "clear_history",
    "aggregate_stats",
]
