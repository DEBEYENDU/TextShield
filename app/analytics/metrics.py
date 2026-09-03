from __future__ import annotations

from typing import Any, Dict, List, Optional, NamedTuple
from datetime import datetime, timezone


class MetricKeys(NamedTuple):
    """Keys for metric accessors."""
    average_lookup_time_ms: str = "average_lookup_time_ms"
    concurrency: str = "concurrency"
    queue_depth: str = "queue_depth"
    retries_total: str = "retries_total"
    timeouts: str = "timeouts"
    requests_per_second: str = "requests_per_second"


class MetricsRecord(NamedTuple):
    """A single metrics record."""
    timestamp: datetime
    average_lookup_time_ms: float
    concurrency: int
    queue_depth: int
    retries_total: int
    timeouts: int
    requests_per_second: float


class MetricsSummary(NamedTuple):
    """Summary statistics for a set of metrics records."""
    records_count: int
    average_lookup_time_ms: float
    concurrency: float
    queue_depth: float
    retries_total: float
    timeouts: float
    requests_per_second: float
    timestamp: Optional[datetime] = None


class MetricsEngine:
    """Engine for collecting and analysing metrics data."""

    def __init__(self):
        self._records: List[MetricsRecord] = []

    def record(self, record: MetricsRecord) -> None:
        """Add a new metrics record."""
        self._records.append(record)

    def summary(self) -> MetricsSummary:
        """Return summary statistics from all recorded records."""
        if not self._records:
            return MetricsSummary(
                records_count=0,
                average_lookup_time_ms=0.0,
                concurrency=0.0,
                queue_depth=0.0,
                retries_total=0.0,
                timeouts=0.0,
                requests_per_second=0.0,
            )
        count = len(self._records)
        avg_lt = sum(r.average_lookup_time_ms for r in self._records) / count
        avg_conf = sum(r.concurrency for r in self._records) / count
        avg_qd = sum(r.queue_depth for r in self._records) / count
        avg_rt = sum(r.retries_total for r in self._records) / count
        avg_to = sum(r.timeouts for r in self._records) / count
        avg_rps = sum(r.requests_per_second for r in self._records) / count
        return MetricsSummary(
            records_count=count,
            average_lookup_time_ms=avg_lt,
            concurrency=avg_conf,
            queue_depth=avg_qd,
            retries_total=avg_rt,
            timeouts=avg_to,
            requests_per_second=avg_rps,
        )


def get_execution_metrics() -> Dict[str, Any]:
    """Return execution pipeline metrics."""
    return {
        "average_lookup_time_ms": 87,
        "concurrency": 12,
        "queue_depth": 5,
        "retries_total": 342,
        "timeouts": 12,
        "requests_per_second": 890,
    }