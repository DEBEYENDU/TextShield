"""Compatibility re-export: storage subpackage entry points."""

from __future__ import annotations

from knowledge_pipeline.storage.document_store import DocumentStore, ProcessedStore

__all__ = ["DocumentStore", "ProcessedStore"]
