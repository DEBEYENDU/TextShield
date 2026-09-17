"""Document manifest: knowledge_manifest.json tracking per-document state."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_MANIFEST = "knowledge_base/knowledge_manifest.json"


@dataclass
class ManifestEntry:
    doc_id: str
    file_hash: str
    last_modified: float
    embedding_version: str = "v1"
    chunk_count: int = 0
    indexed: bool = False
    validation_status: str = "pending"
    category: str = "general"
    size: int = 0
    source_path: str = ""
    chunk_ids: list[str] = field(default_factory=list)


class Manifest:
    """JSON-backed manifest mapping doc_id -> ManifestEntry."""

    def __init__(self, path: Path | str = DEFAULT_MANIFEST):
        self.path = Path(path)
        self.entries: dict[str, ManifestEntry] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                docs = raw.get("documents", raw) if isinstance(raw, dict) else {}
                for doc_id, item in docs.items():
                    if isinstance(item, dict):
                        item.setdefault("doc_id", doc_id)
                        try:
                            self.entries[doc_id] = ManifestEntry(**{
                                k: item.get(k, v) for k, v in {
                                    "doc_id": doc_id, "file_hash": "", "last_modified": 0.0,
                                    "embedding_version": "v1", "chunk_count": 0,
                                    "indexed": False, "validation_status": "pending",
                                    "category": "general", "size": 0, "source_path": "",
                                    "chunk_ids": []}.items()})
                        except TypeError:
                            continue
            except Exception:
                self.entries = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "3.0",
            "updated_at": time.time(),
            "document_count": len(self.entries),
            "documents": {k: asdict(v) for k, v in self.entries.items()},
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, doc_id: str) -> ManifestEntry | None:
        return self.entries.get(doc_id)

    def upsert(self, entry: ManifestEntry) -> None:
        self.entries[entry.doc_id] = entry

    def remove(self, doc_id: str) -> None:
        self.entries.pop(doc_id, None)

    def lookup_by_hash(self, file_hash: str) -> ManifestEntry | None:
        for entry in self.entries.values():
            if entry.file_hash == file_hash:
                return entry
        return None

    def as_incremental_map(self) -> dict:
        """Return {path, name, stem, doc_id -> {file_hash, last_modified}} for the loader."""
        mapping: dict = {}
        for doc_id, entry in self.entries.items():
            info = {"file_hash": entry.file_hash, "last_modified": entry.last_modified}
            mapping[doc_id] = info
            if entry.source_path:
                mapping[entry.source_path] = info
                p = Path(entry.source_path)
                mapping[p.name] = info
                mapping[p.stem] = info
        return mapping
