"""Route module: statistics and model information."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.container import ServiceRegistry, get_request_registry
from app.schemas.analytics import ModelInfoResponse, StatsResponse

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def stats(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Aggregate analytics computed from stored history."""
    return registry.get("analytics")()


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(registry: ServiceRegistry = Depends(get_request_registry)) -> dict:
    """Return ML model metadata and evaluation metrics."""
    return registry.get("models").get_model_info()
