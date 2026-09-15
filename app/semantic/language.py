"""Transformer-based multilingual language detection.

Provides detect_language_transformer and detect_language with automatic fallback
to script heuristic when transformers are unavailable. NEVER crashes.
"""

from __future__ import annotations

import threading
from typing import Tuple

from app.core.logging import get_logger
from app.semantic.config import config
from app.semantic.semantic_utils import detect_language as script_detect_language

logger = get_logger(__name__)

_lock = threading.Lock()
_model = None


def _load_transformer_model():
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        try:
            from transformers import pipeline
            _model = pipeline("text-classification", model="papluca/xlm-roberta-base-language-detection")
            logger.info("Loaded transformer language detection model")
        except Exception as exc:
            logger.warning("Transformer language detection unavailable: %s", exc)
            _model = None
    return _model


def detect_language_transformer(text: str) -> Tuple[str, float]:
    if not text or len(text.strip()) < config.language.min_text_len:
        return "unknown", 0.0
    model = _load_transformer_model()
    if model is None:
        return script_detect_language(text)
    try:
        result = model(text[:512])
        if isinstance(result, list) and result:
            label = result[0].get("label", "unknown").lower()
            score = float(result[0].get("score", 0.0))
            if label and label != "unknown":
                return label[:2], round(score, 3)
    except Exception as exc:
        logger.warning("Transformer language detection failed: %s", exc)
    return script_detect_language(text)


def detect_language(text: str) -> Tuple[str, float]:
    if config.language.detection_mode == "transformer":
        lang, conf = detect_language_transformer(text)
        if lang != "unknown" and conf >= config.language.confidence_threshold:
            return lang, conf
    if config.language.script_fallback:
        return script_detect_language(text)
    return "unknown", 0.0
