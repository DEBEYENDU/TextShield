"""Embedding providers.

Two providers are supported:

1. ``sentence_transformers`` (preferred)
   Local transformer embeddings (e.g. ``all-MiniLM-L6-v2``, ~90MB, CPU).
   Uses the ``sentence-transformers`` package.

2. ``hashing`` (zero-dependency fallback)
   Deterministic character n-gram hashing into a fixed-size normalized
   vector. Semantic quality is lower than a transformer, but it keeps
   the RAG pipeline fully functional on machines without PyTorch.

The provider is selected by the ``EMBEDDING_PROVIDER`` environment
variable and is used consistently at build time and query time.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

HASHING_DIM = 768
HASHING_NGRAMS = (2, 4)


class EmbeddingProvider(ABC):
    name: str = "base"

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return a float32 matrix of shape (len(texts), dimension)."""

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


class HashingEmbeddings(EmbeddingProvider):
    """Deterministic character n-gram hash embeddings (no dependencies)."""

    name = "hashing"

    def __init__(self, dim: int = HASHING_DIM, ngrams: tuple[int, int] = HASHING_NGRAMS):
        self._dim = dim
        self._ngrams = ngrams

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self._dim), dtype=np.float32)
        for row, text in enumerate(texts):
            if not text:
                continue
            text = text.lower()
            for start in range(len(text)):
                for size in range(self._ngrams[0], self._ngrams[1] + 1):
                    gram = text[start : start + size]
                    if len(gram) < size:
                        break
                    index = int(
                        np.frombuffer(
                            (gram + "\x01").encode("utf-8"),
                            dtype=np.uint8,
                        ).sum()
                    ) % self._dim
                    vectors[row, index] += 1.0
            norm = np.linalg.norm(vectors[row])
            if norm > 0:
                vectors[row] /= norm
        return vectors


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Local transformer embeddings via the sentence-transformers package."""

    name = "sentence_transformers"

    def __init__(self, model_name: str | None = None):
        import sentence_transformers  # noqa: F401  (raises if unavailable)

        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dim = 384  # overridden after load

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s ...", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            get_dim = getattr(self._model, "get_embedding_dimension", None) or getattr(
                self._model, "get_sentence_embedding_dimension"
            )
            self._dim = get_dim()

    @property
    def dimension(self) -> int:
        self._load()
        return int(self._dim)

    def embed(self, texts: list[str]) -> np.ndarray:
        self._load()
        return np.asarray(self._model.encode(texts, normalize_embeddings=True), dtype=np.float32)


def create_embedding_provider(force: str | None = None) -> EmbeddingProvider:
    """Factory: build the configured embedding provider with fallbacks."""
    requested = (force or settings.EMBEDDING_PROVIDER).lower()
    if requested == "sentence_transformers":
        try:
            return SentenceTransformerEmbeddings()
        except Exception as exc:  # pragma: no cover - depends on install state
            logger.warning("sentence-transformers unavailable (%s), using hashing", exc)
            return HashingEmbeddings()
    if requested == "hashing":
        return HashingEmbeddings()
    raise ValueError(f"Unknown embedding provider: {requested}")