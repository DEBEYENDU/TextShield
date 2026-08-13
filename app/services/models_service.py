"""Models service: ML model availability and metadata."""
from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.core.settings import settings
from app.ml.classifier import classifier

logger = get_logger(__name__)


def is_available() -> bool:
    return settings.MODEL_PATH.exists() and settings.VECTORIZER_PATH.exists()


def get_model_info() -> dict[str, Any]:
    """Model availability + metadata (algorithm, metrics, dataset)."""
    if not is_available():
        return {"available": False, "message": "ML model files are not present."}
    metadata = {}
    try:
        metadata = json.loads(settings.MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.info("No model metadata.json found; returning file-based info")

    metrics = None
    if settings.MODEL_METRICS_PATH.exists():
        try:
            metrics = json.loads(settings.MODEL_METRICS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metrics = None
    return {
        "available": True,
        "algorithm": classifier.algorithm_name or metadata.get("algorithm"),
        "trained_at": metadata.get("trained_at"),
        "dataset": metadata.get("dataset"),
        "label_mapping": metadata.get("label_mapping"),
        "metrics": metrics or metadata.get("metrics"),
        "comparison": metadata.get("comparison"),
    }