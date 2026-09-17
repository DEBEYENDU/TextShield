"""Vector indexing over the existing RAG store (ChromaDB / simple fallback).

Capabilities: insert, update, delete, incremental indexing, batch indexing,
reindex single document, reindex category, rebuild entire database.
RAG-compatible chunk metadata: {source, category, is_example}.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from knowledge_pipeline.ingestion.chunker import Chunk


class VectorIndexer:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else None
        self._store = None

    @property
    def store(self):
        if self._store is None:
            from app.rag.vector_store import open_vector_store

            self._store = (open_vector_store(self.db_path) if self.db_path
                           else open_vector_store())
        return self._store

    def _metas(self, chunks: list[Chunk]) -> list[dict]:
        out = []
        for chunk in chunks:
            meta = dict(chunk.metadata)
            out.append({
                "source": chunk.source or meta.get("source", "unknown"),
                "category": chunk.category or meta.get("category", "general"),
                "is_example": int(bool(meta.get("is_example", False))),
            })
        return out

    def insert(self, chunks: list[Chunk], embeddings: np.ndarray) -> int:
        if not chunks:
            return 0
        self.store.add([c.chunk_id for c in chunks], np.asarray(embeddings, dtype=np.float32),
                       [c.text for c in chunks], self._metas(chunks))
        try:
            self.store.save_structure(self._merge_structure(len(chunks)))
        except Exception:
            pass
        return len(chunks)

    def _merge_structure(self, added: int) -> dict:
        from app.rag.vector_store import describe_store

        info = describe_store(self.store.path) or {}
        info["chunk_count"] = int(info.get("chunk_count", 0)) + added
        return info

    def delete_by_ids(self, chunk_ids: list[str]) -> int:
        """Simple fallback store has no per-id delete; rebuild without ids.

        ChromaDB path uses collection.delete. Returns number of ids dropped.
        """
        if not chunk_ids:
            return 0
        store = self.store
        if hasattr(store, "_collection") and getattr(store, "_collection", None) is not None:
            try:
                store._collection.delete(ids=chunk_ids)
                return len(chunk_ids)
            except Exception:
                pass
        # Fallback: filter in-memory store and re-persist.
        if hasattr(store, "_ids"):
            keep = [i for i, cid in enumerate(store._ids) if cid not in set(chunk_ids)]
            removed = len(store._ids) - len(keep)
            store._ids = [store._ids[i] for i in keep]
            store._documents = [store._documents[i] for i in keep]
            store._metadatas = [store._metadatas[i] for i in keep]
            if getattr(store, "_embeddings", None) is not None:
                store._embeddings = store._embeddings[keep] if keep else None
            store._persist()
            return removed
        return 0

    def update(self, old_chunk_ids: list[str], chunks: list[Chunk],
               embeddings: np.ndarray) -> int:
        self.delete_by_ids(old_chunk_ids)
        return self.insert(chunks, embeddings)

    def batch_index(self, batches: list[tuple[list[Chunk], np.ndarray]]) -> int:
        total = 0
        for chunks, embeddings in batches:
            total += self.insert(chunks, embeddings)
        return total

    def reindex_single(self, old_chunk_ids: list[str], chunks: list[Chunk],
                       embeddings: np.ndarray) -> int:
        return self.update(old_chunk_ids, chunks, embeddings)

    def reindex_category(self, category: str, chunks: list[Chunk],
                         embeddings: np.ndarray) -> int:
        store = self.store
        existing: list[str] = []
        if hasattr(store, "_ids") and hasattr(store, "_metadatas"):
            existing = [cid for cid, meta in zip(store._ids, store._metadatas)
                        if meta.get("category") == category]
        elif hasattr(store, "_collection") and getattr(store, "_collection", None) is not None:
            try:
                got = store._collection.get(where={"category": category})
                existing = got.get("ids", [])
            except Exception:
                existing = []
        if existing:
            self.delete_by_ids(existing)
        return self.insert(chunks, embeddings)

    def rebuild(self, chunks: list[Chunk], embeddings: np.ndarray, info: dict) -> dict:
        self.store.delete_all()
        self.insert(chunks, embeddings)
        full = dict(info)
        full["chunk_count"] = len(chunks)
        try:
            self.store.save_structure(full)
        except Exception:
            pass
        # Invalidate retriever status cache so RAG sees the new build.
        try:
            from app.rag.retriever import retriever

            retriever.invalidate_cache()
        except Exception:
            pass
        return full

    @property
    def count(self) -> int:
        try:
            return int(self.store.count)
        except Exception:
            return 0
