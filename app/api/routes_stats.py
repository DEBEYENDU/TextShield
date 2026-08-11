"""Route module: statistics and model information."""
from __future__ import annotations

import json

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger
from app.database import database as db
from app.schemas.analysis import ModelInfoResponse, StatsResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def stats() -> dict:
    """Aggregate analytics computed from stored history."""
    return db.aggregate_stats()


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> dict:
    """Return ML model metadata and evaluation metrics."""
    if not settings.MODEL_METADATA_PATH.exists():
        return {
            "available": False,
            "message": "Model metadata not found. Run `python scripts/train_model.py`.",
        }
    try:
        metadata = json.loads(settings.MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Cannot read model metadata: %s", exc)
        return {"available": False, "message": "Model metadata is unreadable."}

    metrics = None
    if settings.MODEL_METRICS_PATH.exists():
        try:
            metrics = json.loads(settings.MODEL_METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            metrics = None

    return {
        "available": True,
        "algorithm": metadata.get("algorithm"),
        "trained_at": metadata.get("trained_at"),
        "dataset": metadata.get("dataset"),
        "label_mapping": metadata.get("label_mapping"),
        "metrics": metrics or metadata.get("metrics"),
        "comparison": metadata.get("comparison"),
    }