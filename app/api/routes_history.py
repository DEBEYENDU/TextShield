"""Route module: history endpoints (list / delete / clear)."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.database import database as db
from app.schemas.analysis import HistoryEntry, HistoryResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def list_history(
    input_type: str | None = Query(default=None),
    classification: Literal["SPAM", "HAM"] | None = Query(default=None),
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: str = Query(default="timestamp"),
    direction: Literal["asc", "desc"] = Query(default="desc"),
) -> dict:
    """List analysis history with filtering, sorting and pagination."""
    filters = {
        "input_type": input_type,
        "classification": classification,
        "risk_level": risk_level,
    }
    items, total = db.query_history(
        filters, limit=limit, offset=offset, order_by=order_by, direction=direction
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.delete("/{entry_id}")
def delete_entry(entry_id: int) -> dict:
    """Delete a single history entry."""
    if not db.delete_history_entry(entry_id):
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"deleted": True, "id": entry_id}


@router.delete("")
def clear_all_history() -> dict:
    """Delete all history entries."""
    deleted = db.clear_history()
    logger.info("History cleared: %d rows deleted", deleted)
    return {"deleted": True, "rows_deleted": deleted}