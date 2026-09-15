"""Transformer model abstraction for semantic intelligence.

Provides lazy loading of sentence-transformers and optional Hugging Face
models for classification / intent / similarity. Always falls back gracefully.
"""

from __future__ import annotations

import threading
from typing import Any

from app.core.logging import get_logger
from app.semantic.config import config

logger = get_logger(__name__)

_lock = threading.Lock()
_classifier = None
_encoder = None


def _load_encoder():
    global _encoder
    if _encoder is not None:
        return _encoder
    with _lock:
        if _encoder is not None:
            return _encoder
        try:
            from sentence_transformers import SentenceTransformer
            device = config.transformer.device
            if device == "auto":
                device = "cpu"
            _encoder = SentenceTransformer(config.transformer.model_name, device=device)
            logger.info("Loaded transformer encoder %s", config.transformer.model_name)
        except Exception as exc:
            logger.warning("Transformer encoder unavailable: %s", exc)
            _encoder = None
    return _encoder


def encode_texts(texts: list[str]) -> list[list[float]]:
    encoder = _load_encoder()
    if encoder is None:
        from app.semantic.embedding_service import embedding_service
        return embedding_service.embed(texts)
    try:
        embeddings = encoder.encode(
            texts,
            normalize_embeddings=config.transformer.normalize_embeddings,
        )
        return [list(map(float, e)) for e in embeddings]
    except Exception as exc:
        logger.warning("Transformer encode failed: %s", exc)
        from app.semantic.embedding_service import embedding_service
        return embedding_service.embed(texts)


def similarity_score(text_a: str, text_b: str) -> float:
    import math
    vec_a = encode_texts([text_a])[0]
    vec_b = encode_texts([text_b])[0]
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in vec_b)) or 1.0
    score = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, score))
