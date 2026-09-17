"""End-to-end ingestion orchestrator: discover -> parse -> clean -> metadata
-> validate -> deduplicate -> chunk -> embed -> index -> manifest.

Incremental by default: unchanged documents are skipped via the manifest.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from knowledge_pipeline.embeddings.embedding_manager import EmbeddingManager
from knowledge_pipeline.indexing.incremental import IncrementalTracker
from knowledge_pipeline.indexing.manifest import Manifest, ManifestEntry
from knowledge_pipeline.indexing.vector_indexer import VectorIndexer
from knowledge_pipeline.ingestion.chunker import ChunkManager
from knowledge_pipeline.ingestion.cleaner import DocumentCleaner
from knowledge_pipeline.ingestion.deduplicator import Deduplicator
from knowledge_pipeline.ingestion.loader import DocumentLoader
from knowledge_pipeline.ingestion.metadata import MetadataExtractor
from knowledge_pipeline.ingestion.parser import parse_file
from knowledge_pipeline.ingestion.validator import DocumentValidator
from knowledge_pipeline.monitoring.performance import PerformanceMonitor
from knowledge_pipeline.monitoring.statistics import PipelineStatistics
from knowledge_pipeline.storage.document_store import DocumentStore, ProcessedStore

logger = logging.getLogger("knowledge_pipeline")


class IngestionPipeline:
    """Configurable pipeline; safe to run repeatedly (incremental)."""

    def __init__(self, kb_root: Path | str = "knowledge_base",
                 manifest_path: Path | str | None = None,
                 provider: str = "hashing", chunk_size: int = 700,
                 chunk_overlap: int = 100, chunk_strategy: str = "paragraph",
                 batch_size: int = 32, min_length: int = 60,
                 db_path: Path | str | None = None,
                 dry_run: bool = False, verbose: bool = False,
                 force: bool = False):
        self.kb_root = Path(kb_root)
        self.manifest = Manifest(manifest_path or (self.kb_root / "knowledge_manifest.json"))
        self.tracker = IncrementalTracker(self.manifest)
        self.cleaner = DocumentCleaner()
        self.meta_extractor = MetadataExtractor()
        self.validator = DocumentValidator(min_length=min_length)
        self.dedup = Deduplicator()
        for entry in self.manifest.entries.values():
            if entry.file_hash:
                self.dedup.load_known({entry.file_hash: entry.doc_id})
        self.chunker = ChunkManager(chunk_size, chunk_overlap, chunk_strategy)
        self.embedder = EmbeddingManager(provider, batch_size=batch_size)
        self.indexer = VectorIndexer(db_path)
        self.doc_store = DocumentStore()
        self.proc_store = ProcessedStore()
        self.dry_run = dry_run
        self.verbose = verbose
        self.force = force
        self.perf = PerformanceMonitor()

    def _log(self, message: str, *args) -> None:
        if self.verbose:
            logger.info(message, *args)

    def run(self, file: Path | str | None = None, folder: Path | str | None = None,
            category: str | None = None) -> dict:
        stats = PipelineStatistics()
        target = Path(file) if file else (Path(folder) if folder else self.kb_root)
        loader = DocumentLoader(target, category=category)
        with self.perf.stage("discover"):
            discovered = loader.discover()
        stats.discovered = len(discovered)
        stats.skipped_unsupported = len(loader.skipped)
        for skipped in loader.skipped:
            self._log("skipped unsupported format: %s", skipped)
            logger.info("documents skipped: %s (unsupported)", skipped)

        if self.force:
            plan_add = discovered
            plan_update: list = []
            plan_delete: list[str] = []
        else:
            with self.perf.stage("change_detection"):
                plan = self.tracker.plan(discovered)
            plan_add, plan_update = plan.to_add, plan.to_update
            plan_delete = plan.to_delete
            stats.skipped_unchanged = plan.unchanged
        logger.info("documents discovered: %d (new=%d updated=%d unchanged=%d deleted=%d)",
                    len(discovered), len(plan_add), len(plan_update), stats.skipped_unchanged,
                    len(plan_delete))

        # Handle deletions
        for doc_id in plan_delete:
            entry = self.manifest.get(doc_id)
            if entry and not self.dry_run:
                with self.perf.stage("vector_delete"):
                    removed = self.indexer.delete_by_ids(entry.chunk_ids)
                stats.vectors_deleted += removed
                self.manifest.remove(doc_id)
                stats.manifest_updates += 1
                logger.info("vector deletion: %s (%d chunks)", doc_id, removed)

        for item in plan_add + plan_update:
            is_update = item in plan_update
            try:
                self._process_one(item, stats, is_update)
            except Exception as exc:
                stats.errors.append(f"{item.path}: {exc}")
                logger.error("processing failed for %s: %s", item.path, exc)

        if not self.dry_run:
            with self.perf.stage("manifest_update"):
                self.manifest.save()
        stats.finish()
        summary = stats.log_summary(logger)
        self._log("%s", summary)
        result = stats.to_dict()
        result["performance"] = self.perf.report()
        result["embedding"] = self.embedder.stats()
        result["dry_run"] = self.dry_run
        return result

    def _process_one(self, item, stats: PipelineStatistics, is_update: bool) -> None:
        with self.perf.stage("parse"):
            doc = parse_file(item.path, category=item.category)
        stats.parsed += 1
        self._log("parsed: %s (%s)", doc.doc_id, doc.extension)

        with self.perf.stage("clean"):
            cleaned = self.cleaner.clean(doc.text)
        if not cleaned:
            stats.parse_failures += 1
            logger.warning("validation failure: %s empty after cleaning", doc.doc_id)
            return

        with self.perf.stage("metadata"):
            metadata, meta_warnings = self.meta_extractor.extract(
                doc.doc_id, doc.title, cleaned, str(item.path), item.category, doc.raw_metadata)
        meta_dict = MetadataExtractor.to_dict(metadata)
        meta_dict["_warnings"] = meta_warnings + doc.warnings

        with self.perf.stage("validate"):
            report = self.validator.validate(doc.doc_id, metadata.title, cleaned, meta_dict)
        for issue in report.issues:
            level = "validation failure" if issue.level == "error" else "validation warning"
            logger.info("%s: %s [%s] %s", level, doc.doc_id, issue.code, issue.message)
        if not report.valid:
            stats.validation_failures += 1
            if not self.force:
                return

        with self.perf.stage("deduplicate"):
            dup, original = self.dedup.is_duplicate(doc.doc_id, cleaned)
        if dup and original != doc.doc_id and not self.force:
            stats.skipped_duplicates += 1
            logger.info("documents skipped: %s (duplicate of %s)", doc.doc_id, original)
            return

        with self.perf.stage("chunk"):
            chunks = self.chunker.chunk(doc.doc_id, cleaned, meta_dict)
        stats.chunks_created += len(chunks)
        self._log("chunking: %s -> %d chunks (%s)", doc.doc_id, len(chunks), self.chunker.strategy)

        if self.dry_run:
            logger.info("dry-run: would index %s (%d chunks)", doc.doc_id, len(chunks))
            return

        with self.perf.stage("embed"):
            embeddings = self.embedder.embed([c.text for c in chunks])
        stats.embeddings_created += len(chunks)
        stats.cache_hits = self.embedder.cache.hits
        stats.cache_misses = self.embedder.cache.misses
        logger.info("embedding creation: %s %d vectors (hits=%d misses=%d)",
                    doc.doc_id, len(chunks), self.embedder.cache.hits, self.embedder.cache.misses)

        with self.perf.stage("index"):
            if is_update:
                old_ids = (self.manifest.get(doc.doc_id).chunk_ids
                           if self.manifest.get(doc.doc_id) else [])
                count = self.indexer.update(old_ids, chunks, embeddings)
                stats.vectors_updated += count
                logger.info("vector update: %s (%d chunks)", doc.doc_id, count)
            else:
                count = self.indexer.insert(chunks, embeddings)
                stats.vectors_inserted += count
                logger.info("vector insertion: %s (%d chunks)", doc.doc_id, count)

        with self.perf.stage("store"):
            try:
                self.doc_store.put(item.path, item.category)
                self.proc_store.put(doc.doc_id, cleaned, chunks, meta_dict)
            except Exception as exc:
                logger.warning("artifact store failed for %s: %s", doc.doc_id, exc)

        # Manifest update
        self.manifest.upsert(ManifestEntry(
            doc_id=doc.doc_id, file_hash=item.sha256, last_modified=item.mtime,
            embedding_version=self.embedder.cache.version, chunk_count=len(chunks),
            indexed=True, validation_status="valid" if report.valid else "forced",
            category=item.category, size=item.size, source_path=str(item.path),
            chunk_ids=[c.chunk_id for c in chunks],
        ))
        stats.manifest_updates += 1
        logger.info("manifest update: %s chunks=%d", doc.doc_id, len(chunks))

    def rebuild_all(self) -> dict:
        """Force full rebuild: clear vector store, reset manifest index flags, reprocess."""
        self.force = True
        try:
            self.indexer.store.delete_all()
        except Exception as exc:
            logger.warning("vector store clear failed: %s", exc)
        self.validator.reset()
        return self.run()

    def build_info(self) -> dict:
        docs = sum(1 for e in self.manifest.entries.values() if e.indexed)
        chunks = sum(e.chunk_count for e in self.manifest.entries.values())
        categories = sorted({e.category for e in self.manifest.entries.values()})
        return {
            "backend": getattr(self.indexer.store, "backend_name", "unknown"),
            "embedding_provider": self.embedder.provider_name,
            "dimension": self.embedder.dimension,
            "chunk_count": chunks,
            "document_count": docs,
            "categories": categories,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "chunk_size": self.chunker.chunk_size,
            "chunk_overlap": self.chunker.chunk_overlap,
            "chunk_strategy": self.chunker.strategy,
        }
