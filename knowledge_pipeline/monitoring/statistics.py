"""Run statistics: documents discovered/skipped, validation, cache, vectors."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field


@dataclass
class PipelineStatistics:
    discovered: int = 0
    skipped_unsupported: int = 0
    skipped_unchanged: int = 0
    skipped_duplicates: int = 0
    parsed: int = 0
    parse_failures: int = 0
    validation_failures: int = 0
    chunks_created: int = 0
    embeddings_created: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    vectors_inserted: int = 0
    vectors_updated: int = 0
    vectors_deleted: int = 0
    manifest_updates: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    errors: list[str] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = time.time()

    @property
    def elapsed(self) -> float:
        end = self.finished_at or time.time()
        return round(end - self.started_at, 3)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["elapsed_seconds"] = self.elapsed
        return data

    def log_summary(self, logger=None) -> str:
        summary = (
            f"discovered={self.discovered} parsed={self.parsed} "
            f"skipped(unsupported={self.skipped_unsupported} "
            f"unchanged={self.skipped_unchanged} duplicates={self.skipped_duplicates}) "
            f"validation_failures={self.validation_failures} chunks={self.chunks_created} "
            f"embeddings={self.embeddings_created} cache(hits={self.cache_hits} "
            f"misses={self.cache_misses}) vectors(+{self.vectors_inserted} "
            f"~{self.vectors_updated} -{self.vectors_deleted}) "
            f"manifest={self.manifest_updates} elapsed={self.elapsed}s"
        )
        if logger is not None:
            try:
                logger.info("Ingestion summary: %s", summary)
            except Exception:
                pass
        return summary
