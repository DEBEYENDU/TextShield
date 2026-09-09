"""Raw document store (content-addressed) and processed artifact store."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


class DocumentStore:
    """Persist raw document bytes keyed by SHA256 for audit/replay."""

    def __init__(self, root: Path | str = "vector_db/document_store"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, source: Path, category: str = "general") -> dict:
        data = Path(source).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        dest_dir = self.root / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{digest}{Path(source).suffix.lower()}"
        if not dest.exists():
            shutil.copyfile(source, dest)
        return {"hash": digest, "stored_path": str(dest), "size": len(data)}

    def get(self, digest: str, category: str = "general") -> Path | None:
        for hit in (self.root / category).glob(f"{digest}.*"):
            return hit
        for hit in self.root.rglob(f"{digest}.*"):
            return hit
        return None


class ProcessedStore:
    """Persist cleaned text + chunk JSON per document for debugging/replay."""

    def __init__(self, root: Path | str = "vector_db/processed_store"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, doc_id: str, cleaned_text: str, chunks: list,
            metadata: dict) -> Path:
        safe = doc_id.replace(":", "__").replace("/", "_")
        dest = self.root / f"{safe}.json"
        payload = {
            "doc_id": doc_id,
            "metadata": metadata,
            "cleaned_text": cleaned_text,
            "chunks": [
                {"chunk_id": c.chunk_id, "text": c.text, "index": c.index,
                 "strategy": c.strategy, "char_start": c.char_start,
                 "char_end": c.char_end} for c in chunks
            ],
        }
        dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return dest

    def get(self, doc_id: str) -> dict | None:
        safe = doc_id.replace(":", "__").replace("/", "_")
        path = self.root / f"{safe}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None
