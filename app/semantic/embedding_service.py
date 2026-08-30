"""Semantic Understanding Engine — embedding service.

Wraps Sentence Transformers behind a small, swappable interface:

* model name, device, batch size and cache size are configurable via
  environment (``app.core.settings``)
* optional embedding cache (LRU) keyed by normalized text hash — identical
  messages are never re-embedded
* deterministic ``fallback_hashing`` embedder when sentence-transformers
  (or the model) is unavailable — the engine never crashes on load
* thread-safe lazy model loading (first call pays the cost)

The service is independent of RAG: it has its own model handle, cache
and fallback path.
"""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Any, Sequence

from app.core.logging import get_logger
from app.core.settings import settings
from app.semantic.semantic_utils import preprocess_text

logger = get_logger(__name__)

_PROVIDER_ST = "sentence_transformers"
_PROVIDER_FALLBACK = "fallback_hashing"


def _stable_hash(text: str) -> int:
    """Deterministic 64-bit hash (Python's hash() is salted)."""
    return int.from_bytes(
        hashlib.sha256(text.encode("utf-8", errors="replace")).digest()[:8],
        byteorder="big",
    )


class _HashingEmbedder:
    """Zero-dependency deterministic embedder (fallback).

    Word + character n-gram hashing into a fixed-dimension vector,
    L2-normalized. Deterministic across processes. Semantic quality is
    lower than sentence-transformers — it exists so the engine always
    works.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension
        self._word_grams = [1, 2]
        self._char_grams = [3, 4]

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        import math

        vectors = []
        for text in texts:
            vector = [0.0] * self._dimension
            cleaned = preprocess_text(text).lower()
            tokens = [t.strip(".,;:!?()[]{}\"'<>-") for t in cleaned.split()]
            for gram_size in self._word_grams:
                for i in range(len(tokens) - gram_size + 1):
                    key = "_".join(tokens[i : i + gram_size])
                    idx = _stable_hash(key) % self._dimension
                    vector[idx] += 1.0
            for gram_size in self._char_grams:
                for i in range(len(cleaned) - gram_size + 1):
                    key = cleaned[i : i + gram_size]
                    idx = _stable_hash(key) % self._dimension
                    vector[idx] += 1.0
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            vectors.append([v / norm for v in vector])
        return vectors


class EmbeddingService:
    """Configurable embedding service with LRU cache and fallback."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int | None = None,
        cache_size: int | None = None,
        fallback_dimension: int | None = None,
    ) -> None:
        self._model_name = model_name or settings.SEMANTIC_EMBEDDING_MODEL
        self._device = (device or settings.SEMANTIC_DEVICE).lower()
        self._batch_size = batch_size or settings.SEMANTIC_BATCH_SIZE
        self._cache_size = cache_size or settings.SEMANTIC_CACHE_SIZE
        self._fallback_dimension = (
            fallback_dimension or settings.SEMANTIC_EMBEDDING_DIMENSION
        )
        self._model: Any = None
        self._fallback = _HashingEmbedder(self._fallback_dimension)
        self._provider: str = _PROVIDER_ST
        self._cache: OrderedDict[int, list[float]] = OrderedDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------ loading
    def _load_model(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer

                device = self._resolve_device()
                logger.info(
                    "Loading semantic embedding model %s (device=%s)",
                    self._model_name,
                    device,
                )
                self._model = SentenceTransformer(self._model_name, device=device)
                self._provider = _PROVIDER_ST
            except Exception as exc:  # pragma: no cover - environment dependent
                logger.warning(
                    "Sentence-transformers unavailable (%s); using fallback hashing "
                    "embedder (dim=%d)",
                    exc,
                    self._fallback_dimension,
                )
                self._model = None
                self._provider = _PROVIDER_FALLBACK

    def _resolve_device(self) -> str:
        if self._device == "cpu":
            return "cpu"
        if self._device in {"cuda", "gpu"}:
            return "cuda"
        if self._device == "mps":
            return "mps"
        # auto
        try:
            import torch  # noqa: F401

            if torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"

    # ------------------------------------------------------------ caching
    def _cache_get(self, key: int) -> list[float] | None:
        value = self._cache.get(key)
        if value is not None:
            self._cache.move_to_end(key)
        return value

    def _cache_put(self, key: int, value: list[float]) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def cache_info(self) -> dict:
        return {"size": len(self._cache), "max_size": self._cache_size}

    # ------------------------------------------------------------ encoding
    @property
    def provider(self) -> str:
        if self._model is None:
            self._load_model()
        return self._provider

    @property
    def dimension(self) -> int:
        if self._provider == _PROVIDER_ST:
            self._load_model()
            return int(self._model.get_sentence_embedding_dimension())
        return self._fallback_dimension

    def is_ready(self) -> bool:
        return True  # fallback always available

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts (cached per unique normalized text)."""
        if not texts:
            return []
        keys = [_stable_hash(preprocess_text(t)) for t in texts]
        with self._lock:
            hits = {k: self._cache_get(k) for k in keys}
            missing = [t for t, k in zip(texts, keys) if hits[k] is None]
        if missing:
            vectors = self._encode_missing(missing)
            with self._lock:
                for text, vector in zip(missing, vectors):
                    self._cache_put(_stable_hash(preprocess_text(text)), vector)
        with self._lock:
            return [self._cache_get(k) for k in keys]  # type: ignore[list-item]

    def _encode_missing(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        try:
            if self._model is not None:
                raw = self._model.encode(
                    texts,
                    batch_size=self._batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                return [list(map(float, row)) for row in raw]
            return self._fallback.encode(texts)
        except Exception as exc:  # pragma: no cover - runtime env issues
            logger.warning("Embedding failed (%s); using fallback embedder", exc)
            self._model = None
            self._provider = _PROVIDER_FALLBACK
            return self._fallback.encode(texts)

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text (cached)."""
        return self.embed([text])[0]


# Module-level singleton (lazy model loading).
embedding_service = EmbeddingService()
