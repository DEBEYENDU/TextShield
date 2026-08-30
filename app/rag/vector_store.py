"""Local vector database.

Backends (in preference order):
1. **ChromaDB** - persistent, production-grade local vector store.
2. **SimpleVectorStore** - zero-dependency fallback (numpy + JSON) so
   the RAG pipeline still works on machines without chromadb.

Both implement the same interface. The store is built by
``scripts/build_knowledge_base.py`` and is *not* rebuilt on app start.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

STRUCTURE_FILE = "structure.json"


def structure_file(db_path: Path) -> Path:
    return db_path / STRUCTURE_FILE


def describe_store(db_path: Path) -> dict | None:
    """Return persisted store metadata (doc count, build time) if present."""
    path = structure_file(db_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


class VectorStore(ABC):
    """Common interface implemented by both backends."""

    backend_name = "base"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def add(
        self,
        ids: list[str],
        embeddings: np.ndarray,
        documents: list[str],
        metadatas: list[dict],
    ) -> None: ...

    @abstractmethod
    def query(self, embedding: np.ndarray, top_k: int = 4) -> list[dict]:
        """Return top_k hits: [{id, document, metadata, score}]."""
        ...

    @abstractmethod
    def delete_all(self) -> None: ...

    def save_structure(self, info: dict) -> None:
        structure_file(self.path).write_text(
            json.dumps(info, indent=2), encoding="utf-8"
        )


class SimpleVectorStore(VectorStore):
    """Numpy-based fallback store: vectors.npy + metadata.json + ids.json."""

    backend_name = "simple"

    VECTORS_FILE = "vectors.npy"
    META_FILE = "metadata.json"
    IDS_FILE = "ids.json"

    def __init__(self, path: Path):
        super().__init__(path)
        self._ids: list[str] = []
        self._documents: list[str] = []
        self._metadatas: list[dict] = []
        self._embeddings: np.ndarray | None = None
        self._load()

    def _load(self) -> None:
        ids_file = self.path / self.IDS_FILE
        if ids_file.exists():
            self._ids = json.loads(ids_file.read_text(encoding="utf-8"))
        meta_file = self.path / self.META_FILE
        if meta_file.exists():
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            self._documents = data.get("documents", [])
            self._metadatas = data.get("metadatas", [])
        vectors_file = self.path / self.VECTORS_FILE
        if vectors_file.exists():
            self._embeddings = np.load(vectors_file)

    @property
    def count(self) -> int:
        return len(self._ids)

    def add(
        self,
        ids: list[str],
        embeddings: np.ndarray,
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._ids.extend(ids)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        new = np.asarray(embeddings, dtype=np.float32)
        if self._embeddings is None:
            self._embeddings = new
        else:
            self._embeddings = np.vstack([self._embeddings, new])
        self._persist()

    def query(self, embedding: np.ndarray, top_k: int = 4) -> list[dict]:
        if self._embeddings is None or self._embeddings.shape[0] == 0:
            return []
        query_vec = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        # cosine similarity on normalized vectors == dot product
        scores = (self._embeddings @ query_vec.T).ravel()
        top = int(min(top_k, len(scores)))
        order = np.argsort(-scores)[:top]
        results = []
        for index in order:
            results.append(
                {
                    "id": self._ids[index],
                    "document": self._documents[index],
                    "metadata": self._metadatas[index],
                    "score": round(float(scores[index]), 4),
                }
            )
        return results

    def delete_all(self) -> None:
        self._ids, self._documents, self._metadatas = [], [], []
        self._embeddings = None
        for file in (
            self.path / self.VECTORS_FILE,
            self.path / self.META_FILE,
            self.path / self.IDS_FILE,
            self.path / STRUCTURE_FILE,
        ):
            file.unlink(missing_ok=True)

    def _persist(self) -> None:
        if self._embeddings is not None:
            np.save(self.path / self.VECTORS_FILE, self._embeddings)
        (self.path / self.IDS_FILE).write_text(json.dumps(self._ids), encoding="utf-8")
        (self.path / self.META_FILE).write_text(
            json.dumps({"documents": self._documents, "metadatas": self._metadatas}),
            encoding="utf-8",
        )


class ChromaVectorStore(VectorStore):
    """ChromaDB persistent client wrapper (primary backend)."""

    backend_name = "chromadb"
    COLLECTION = "textshield_knowledge"

    def __init__(self, path: Path):
        super().__init__(path)
        self._client = None
        self._collection = None
        self._load()

    def _load(self):
        try:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.path))
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION, metadata={"hnsw:space": "cosine"}
            )
        except Exception as exc:
            logger.warning("ChromaDB unavailable (%s)", exc)
            self._client = None

    @property
    def ready(self) -> bool:
        return self._collection is not None

    @property
    def count(self) -> int:
        if not self.ready:
            return 0
        return self._collection.count()

    def add(
        self,
        ids: list[str],
        embeddings: np.ndarray,
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        if not self.ready:
            raise RuntimeError("ChromaDB backend not ready")
        self._collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
        )

    def query(self, embedding: np.ndarray, top_k: int = 4) -> list[dict]:
        if not self.ready:
            return []
        hits = self._collection.query(
            query_embeddings=[embedding.tolist()], n_results=top_k
        )
        results = []
        for i, doc_id in enumerate(hits.get("ids", [[]])[0]):
            results.append(
                {
                    "id": doc_id,
                    "document": hits["documents"][0][i],
                    "metadata": hits["metadatas"][0][i],
                    "score": round(1.0 - float(hits["distances"][0][i]), 4),
                }
            )
        return results

    def delete_all(self) -> None:
        if self.ready:
            try:
                self._client.delete_collection(self.COLLECTION)
            except Exception:
                pass
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION, metadata={"hnsw:space": "cosine"}
            )


_backend_cache: dict[str, VectorStore] = {}


def open_vector_store(path: Path | None = None) -> VectorStore:
    """Open the configured vector store, falling back to the simple store."""
    db_path = Path(path or settings.VECTOR_DB_PATH)
    key = str(db_path)
    if key in _backend_cache:
        return _backend_cache[key]
    chroma = ChromaVectorStore(db_path)
    if chroma.ready:
        store: VectorStore = chroma
        logger.info("Vector store backend: chromadb (%s)", db_path)
    else:
        store = SimpleVectorStore(db_path)
        logger.info("Vector store backend: simple (numpy fallback) @ %s", db_path)
    _backend_cache[key] = store
    return store


def available_backend() -> str:
    """Name of the backend that *would* be used (cheap probe)."""
    store = open_vector_store()
    return store.backend_name
