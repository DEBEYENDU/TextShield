"""SHA256 embedding cache — never regenerate unchanged embeddings."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

CACHE_VERSION = "v1"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


class EmbeddingCache:
    """Disk-backed cache: {sha256 -> (embedding, model, created, version)}."""

    def __init__(self, cache_dir: Path | str = "vector_db/embedding_cache",
                 model: str = "hashing", version: str = CACHE_VERSION):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = model
        self.version = version
        self._index_file = self.cache_dir / "index.json"
        self._index: dict[str, dict] = self._load_index()
        self.hits = 0
        self.misses = 0

    def _load_index(self) -> dict:
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        try:
            self._index_file.write_text(json.dumps(self._index), encoding="utf-8")
        except Exception:
            pass

    def _vec_path(self, digest: str) -> Path:
        return self.cache_dir / f"{digest}.npy"

    def get(self, text: str) -> np.ndarray | None:
        digest = text_hash(text)
        entry = self._index.get(digest)
        vec_file = self._vec_path(digest)
        if entry and vec_file.exists() and entry.get("model") == self.model \
                and entry.get("version") == self.version:
            try:
                self.hits += 1
                return np.load(vec_file)
            except Exception:
                pass
        self.misses += 1
        return None

    def put(self, text: str, embedding: np.ndarray) -> str:
        digest = text_hash(text)
        try:
            np.save(self._vec_path(digest), np.asarray(embedding, dtype=np.float32))
            self._index[digest] = {
                "model": self.model,
                "version": self.version,
                "created": time.time(),
                "dim": int(np.asarray(embedding).shape[-1]),
            }
            self._save_index()
        except Exception:
            pass
        return digest

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "entries": len(self._index),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "model": self.model,
            "version": self.version,
        }

    def clear(self) -> None:
        for f in self.cache_dir.glob("*.npy"):
            f.unlink(missing_ok=True)
        self._index = {}
        self._save_index()
        self.hits = self.misses = 0
