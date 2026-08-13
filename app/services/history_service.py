"""History service: query, filter, delete analysis history."""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.database.base import get_connection
from app.database.repositories import history_repository
from app.schemas.history import HistoryEntry, HistoryFilters

logger = get_logger(__name__)

_ALLOWED_ORDER = {"timestamp", "id", "confidence", "classification", "risk_level"}


def list_history(
    filters: HistoryFilters | None = None,
    *,
    order_by: str = "timestamp",
    direction: str = "desc",
) -> dict[str, Any]:
    """Return {items, total, limit, offset} for the history list."""
    f = filters or HistoryFilters()
    if order_by not in _ALLOWED_ORDER:
        order_by = "timestamp"
    direction = "asc" if direction.lower() == "asc" else "desc"
    with get_connection() as conn:
        rows = history_repository.list_all(
            conn,
            limit=f.limit,
            offset=f.offset,
            input_type=f.input_type,
            classification=f.classification,
            risk_level=f.risk_level,
            intent=f.intent,
            order_by=order_by,
            direction=direction,
        )
        total = history_repository.count(
            conn,
            input_type=f.input_type,
            classification=f.classification,
            risk_level=f.risk_level,
            intent=f.intent,
        )
    return {
        "items": [HistoryEntry(**row).model_dump() for row in rows],
        "total": total,
        "limit": f.limit,
        "offset": f.offset,
    }


def delete_entry(entry_id: int) -> bool:
    with get_connection() as conn:
        return history_repository.delete_by_id(conn, entry_id)


def clear_all() -> int:
    with get_connection() as conn:
        return history_repository.clear(conn)


def count_rows() -> int:
    with get_connection() as conn:
        return history_repository.count(conn)
