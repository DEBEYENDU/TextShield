"""Document discovery with incremental support.

Responsibilities: discover files, detect format, skip unsupported formats,
load recursively, track modification timestamps, detect deleted documents,
support incremental ingestion.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from knowledge_pipeline import SUPPORTED_EXTENSIONS


@dataclass
class DiscoveredFile:
    path: Path
    extension: str
    size: int
    mtime: float
    sha256: str = ""
    supported: bool = True
    category: str = "general"


def file_sha256(path: Path, limit_bytes: int = 5_000_000) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        remaining = limit_bytes
        while remaining > 0:
            block = fh.read(min(65536, remaining))
            if not block:
                break
            h.update(block)
            remaining -= len(block)
    return h.hexdigest()


class DocumentLoader:
    """Recursively discover documents under a root folder or single file."""

    def __init__(self, root: Path | str, category: str | None = None,
                 recursive: bool = True):
        self.root = Path(root)
        self.forced_category = category
        self.recursive = recursive
        self.discovered: list[DiscoveredFile] = []
        self.skipped: list[Path] = []

    def discover(self) -> list[DiscoveredFile]:
        self.discovered = []
        self.skipped = []
        if self.root.is_file():
            self._handle_file(self.root, self.root.parent)
        elif self.root.is_dir():
            pattern = "**/*" if self.recursive else "*"
            for path in sorted(self.root.glob(pattern)):
                if path.is_file():
                    self._handle_file(path, self.root)
        return self.discovered

    def _handle_file(self, path: Path, root: Path) -> None:
        ext = path.suffix.lower()
        try:
            rel = path.relative_to(root)
            category = self.forced_category or (rel.parts[0] if len(rel.parts) > 1 else "general")
        except ValueError:
            category = self.forced_category or "general"
        if ext not in SUPPORTED_EXTENSIONS:
            self.skipped.append(path)
            return
        try:
            stat = path.stat()
        except OSError:
            self.skipped.append(path)
            return
        self.discovered.append(
            DiscoveredFile(
                path=path,
                extension=ext,
                size=stat.st_size,
                mtime=stat.st_mtime,
                sha256=file_sha256(path),
                supported=True,
                category=category,
            )
        )

    def detect_deleted(self, known_paths: set[str]) -> list[str]:
        """Return previously-known paths that no longer exist on disk."""
        live = {str(d.path) for d in self.discovered}
        return sorted(p for p in known_paths if p not in live and not os.path.exists(p))

    def filter_incremental(self, manifest: dict) -> list[DiscoveredFile]:
        """Keep only new or modified files according to a manifest mapping.

        manifest: {doc_id or str(path): {"file_hash": ..., "last_modified": ...}}
        """
        out: list[DiscoveredFile] = []
        for item in self.discovered:
            key_variants = {str(item.path), item.path.name, item.path.stem}
            match = None
            for key in key_variants:
                if key in manifest:
                    match = manifest[key]
                    break
            if match is None:
                out.append(item)  # new document
            elif match.get("file_hash") != item.sha256:
                out.append(item)  # modified document
        return out
