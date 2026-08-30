"""Route module: history endpoints (list / delete / clear)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.container import ServiceRegistry, get_request_registry
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.history import HistoryFilters, HistoryResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def list_history(
    input_type: Literal["sms", "text", "email"] | None = Query(default=None),
    classification: Literal["SPAM", "HAM"] | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_by: str = Query(default="timestamp"),
    direction: Literal["asc", "desc"] = Query(default="desc"),
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """List analysis history with filtering, sorting and pagination."""
    filters = HistoryFilters(
        input_type=input_type,
        classification=classification,
        risk_level=risk_level,
        intent=intent,
        limit=limit,
        offset=offset,
    )
    return registry.get("history").list_history(
        filters, order_by=order_by, direction=direction
    )


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int, registry: ServiceRegistry = Depends(get_request_registry)
) -> dict:
    """Delete a single history entry."""
    if not registry.get("history").delete_entry(entry_id):
        raise NotFoundError("History entry not found")
    return {"deleted": True, "id": entry_id}


@router.delete("")
def clear_all_history(
    registry: ServiceRegistry = Depends(get_request_registry),
) -> dict:
    """Delete all history entries."""
    deleted = registry.get("history").clear_all()
    logger.info("History cleared: %d rows deleted", deleted)
    return {"deleted": True, "rows_deleted": deleted}
