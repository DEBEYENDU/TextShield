"""Content deduplication by SHA256 of normalized text."""

from __future__ import annotations

import hashlib


def content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8", errors="ignore")).hexdigest()


class Deduplicator:
    """Track seen content hashes; skip exact duplicates."""

    def __init__(self):
        self._seen: dict[str, str] = {}  # hash -> doc_id
        self.duplicates: list[tuple[str, str]] = []  # (doc_id, original_doc_id)

    def load_known(self, mapping: dict[str, str]) -> None:
        self._seen.update(mapping)

    def is_duplicate(self, doc_id: str, text: str) -> tuple[bool, str]:
        digest = content_hash(text)
        if digest in self._seen:
            original = self._seen[digest]
            if original != doc_id:
                self.duplicates.append((doc_id, original))
                return True, original
            return True, original
        self._seen[doc_id] = digest
        self._seen[digest] = doc_id
        return False, ""

    def reset(self) -> None:
        self._seen.clear()
        self.duplicates.clear()
