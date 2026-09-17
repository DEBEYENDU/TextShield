"""Batch embedding manager with cache, batching and graceful degradation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from knowledge_pipeline.embeddings.embedding_cache import EmbeddingCache
from knowledge_pipeline.embeddings.embedding_provider import (
    BaseEmbeddingProvider,
    create_provider,
)


class EmbeddingManager:
    """Embed texts in batches, reusing cached vectors for unchanged content."""

    def __init__(self, provider: str | BaseEmbeddingProvider = "hashing",
                 batch_size: int = 32, cache_dir: Path | str | None = None,
                 **provider_kwargs):
        if isinstance(provider, str):
            self.provider_name = provider
            self.provider = create_provider(provider, **provider_kwargs)
        else:
            self.provider = provider
            self.provider_name = getattr(provider, "provider_name", "custom")
        self.batch_size = batch_size
        cache_path = Path(cache_dir) if cache_dir else Path("vector_db/embedding_cache")
        self.cache = EmbeddingCache(cache_path, model=self.provider_name)

    @property
    def dimension(self) -> int:
        try:
            return int(self.provider.dimension)
        except Exception:
            return 768

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        vectors: list[np.ndarray | None] = [None] * len(texts)
        pending: list[str] = []
        pending_idx: list[int] = []
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                vectors[i] = np.asarray(cached, dtype=np.float32)
            else:
                pending.append(text)
                pending_idx.append(i)
        for start in range(0, len(pending), self.batch_size):
            batch = pending[start:start + self.batch_size]
            idxs = pending_idx[start:start + self.batch_size]
            try:
                produced = self.provider.embed(batch)
            except Exception:
                # Remote provider not configured -> hashing fallback, never crash.
                fallback = create_provider("hashing")
                produced = fallback.embed(batch)
            for row, vec in zip(idxs, produced):
                vec = np.asarray(vec, dtype=np.float32)
                vectors[row] = vec
                self.cache.put(texts[row], vec)
        matrix = np.vstack([v if v is not None else np.zeros(self.dimension, dtype=np.float32)
                            for v in vectors]).astype(np.float32)
        return matrix

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def stats(self) -> dict:
        info = self.cache.stats()
        info.update({"provider": self.provider_name, "dimension": self.dimension,
                     "batch_size": self.batch_size})
        return info
