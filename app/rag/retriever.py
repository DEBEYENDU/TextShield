"""RAG retrieval: embed the message, search the vector store.

Retrieval results are never fabricated: each hit carries the actual
source document name, category, and the chunk text stored at build time.
"""
from __future__ import annotations

import time as _time
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings import create_embedding_provider
from app.rag.vector_store import describe_store, open_vector_store

logger = get_logger(__name__)

_STATUS_TTL_SECONDS = 5.0


class RetrieverBase(ABC):
    @property
    @abstractmethod
    def is_ready(self) -> bool:
        ...

    @abstractmethod
    def retrieve(self, text: str, top_k: int | None = None) -> list[dict]:
        ...


class Retriever(RetrieverBase):
    """Default retriever: embedding search over the knowledge store."""

    def __init__(self):
        self._store = None
        self._provider = None
        self._status_cache: tuple[float, dict] | None = None

    @property
    def store(self):
        if self._store is None:
            self._store = open_vector_store()
        return self._store

    @property
    def provider(self):
        if self._provider is None:
            self._provider = create_embedding_provider()
        return self._provider

    @property
    def is_ready(self) -> bool:
        return self.status()["ready"]

    def status(self) -> dict:
        """Build status with a short TTL cache (structure.json is on disk)."""
        now = _time.time()
        if self._status_cache and now - self._status_cache[0] < _STATUS_TTL_SECONDS:
            return self._status_cache[1]
        try:
            info = describe_store(self.store.path)
            status = {
                "ready": bool(info and info.get("chunk_count", 0) > 0),
                "backend": self.store.backend_name,
                "embedding_provider": self.provider.name,
                "chunk_count": int(info.get("chunk_count", 0)) if info else 0,
                "document_count": int(info.get("document_count", 0)) if info else 0,
                "categories": info.get("categories", []) if info else [],
                "built_at": info.get("built_at") if info else None,
            }
        except Exception:
            status = {
                "ready": False, "backend": self.store.backend_name,
                "embedding_provider": self.provider.name,
                "chunk_count": 0, "document_count": 0,
                "categories": [], "built_at": None,
            }
        self._status_cache = (now, status)
        return status

    def invalidate_cache(self) -> None:
        """Drop the cached status (call after a knowledge-base rebuild)."""
        self._status_cache = None

    def retrieve(self, text: str, top_k: int | None = None) -> list[dict]:
        """Retrieve top-k knowledge chunks plus closely matching examples."""
        if not self.is_ready or not text.strip():
            return []
        k = top_k or settings.RAG_TOP_K
        try:
            embedding = self.provider.embed_one(text)
            hits = self.store.query(embedding, top_k=k)
            results = []
            for hit in hits:
                metadata = hit.get("metadata", {})
                source = metadata.get("source", "unknown")
                results.append(
                    {
                        "document": hit.get("document", ""),
                        "source": source,
                        "category": metadata.get("category", "general"),
                        "chunk_id": hit.get("id", ""),
                        "score": round(float(hit.get("score", 0.0)), 4),
                        "is_example": bool(metadata.get("is_example", False)),
                    }
                )
            return results
        except Exception as exc:
            logger.error("RAG retrieval failed: %s", exc)
            return []


retriever = Retriever()