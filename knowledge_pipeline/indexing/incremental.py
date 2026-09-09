"""Change detection for incremental ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from knowledge_pipeline.indexing.manifest import Manifest
from knowledge_pipeline.ingestion.loader import DiscoveredFile


@dataclass
class ChangePlan:
    to_add: list[DiscoveredFile] = field(default_factory=list)
    to_update: list[DiscoveredFile] = field(default_factory=list)
    to_delete: list[str] = field(default_factory=list)  # doc_ids
    unchanged: int = 0


class IncrementalTracker:
    """Compare discovered files against the manifest to build a minimal plan."""

    def __init__(self, manifest: Manifest):
        self.manifest = manifest

    def plan(self, discovered: list[DiscoveredFile],
             known_paths: set[str] | None = None) -> ChangePlan:
        plan = ChangePlan()
        live_paths = {str(d.path) for d in discovered}
        for item in discovered:
            entry = (self.manifest.get(f"{item.category}:{item.path.stem}")
                     or self.manifest.lookup_by_hash(item.sha256))
            by_path = None
            for candidate in self.manifest.entries.values():
                if candidate.source_path == str(item.path):
                    by_path = candidate
                    break
            active = by_path or entry
            if active is None:
                plan.to_add.append(item)
            elif active.file_hash != item.sha256:
                plan.to_update.append(item)
            else:
                plan.unchanged += 1
        if known_paths is None:
            known_paths = {e.source_path for e in self.manifest.entries.values() if e.source_path}
        for old in sorted(known_paths):
            if old and old not in live_paths and not Path(old).exists():
                # Find doc_id for the deleted path
                for doc_id, entry in self.manifest.entries.items():
                    if entry.source_path == old:
                        plan.to_delete.append(doc_id)
                        break
        return plan

    def is_unchanged(self, doc_id: str, file_hash: str) -> bool:
        entry = self.manifest.get(doc_id)
        return bool(entry and entry.file_hash == file_hash and entry.indexed)
