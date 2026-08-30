from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

from .config import AnalyticsConfig


class MetricsRecord:
    """A single metrics record with timestamp and values."""

    def __init__(
        self,
        timestamp: datetime,
        metrics: Dict[str, Any],
        record_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.timestamp = timestamp
        self.metrics = metrics
        self.type = record_type
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "metrics": self.metrics,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsRecord":
        from datetime import datetime

        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metrics=data["metrics"],
            record_type=data["type"],
            metadata=data.get("metadata"),
        )


class MetricsSummary:
    """Summary statistics for a set of metrics records."""

    def __init__(
        self,
        records: List[MetricsRecord],
        time_range: Optional[tuple] = None,
    ):
        self.records = records
        self.time_range = time_range

    def count_by_type(self) -> Dict[str, int]:
        from collections import Counter

        counts = Counter(r.type for r in self.records)
        return dict(counts)

    def count_in_range(self, start: datetime, end: datetime) -> int:
        return sum(1 for r in self.records if start <= r.timestamp <= end)

    def average(self, key: str) -> Optional[float]:
        values = [
            r.metrics.get(key, 0.0)
            for r in self.records
            if key in r.metrics and isinstance(r.metrics.get(key), (int, float))
        ]
        if not values:
            return None
        return sum(values) / len(values)

    def percentile(self, key: str, p: float) -> Optional[float]:
        values = sorted(
            [
                r.metrics.get(key, 0.0)
                for r in self.records
                if key in r.metrics and isinstance(r.metrics.get(key), (int, float))
            ]
        )
        if not values:
            return None
        idx = int(len(values) * p)
        idx = min(idx, len(values) - 1)
        return values[idx]

    def by_type(self, record_type: str) -> List[MetricsRecord]:
        return [r for r in self.records if r.type == record_type]


class MetricsEngine:
    """Engine for collecting, storing, and analyzing metrics."""

    def __init__(self, config: Optional[AnalyticsConfig] = None):
        self.config = config or AnalyticsConfig()
        self._records: List[MetricsRecord] = []
        self._index: Dict[str, List[MetricsRecord]] = {}

    def record(
        self,
        metrics: Dict[str, Any],
        record_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a new metrics record."""
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc)
        record = MetricsRecord(timestamp, metrics, record_type, metadata)
        self._records.append(record)
        if record_type not in self._index:
            self._index[record_type] = []
        self._index[record_type].append(record)

        # Enforce retention policy
        if len(self._records) > self.config.max_history_entries:
            self._records.pop(0)
            if record_type in self._index:
                self._index[record_type].pop(0)

    def get_records(self, record_type: Optional[str] = None) -> List[MetricsRecord]:
        """Get records, optionally filtered by type."""
        if record_type:
            return self._index.get(record_type, [])
        return self._records

    def get_summary(self, record_type: Optional[str] = None) -> MetricsSummary:
        """Get a summary of records."""
        records = self.get_records(record_type)
        return MetricsSummary(records)

    def get_recent(
        self, minutes: int = 60, record_type: Optional[str] = None
    ) -> List[MetricsRecord]:
        """Get records from the last N minutes."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        all_records = self.get_records(record_type)
        return [r for r in all_records if r.timestamp >= cutoff]

    def export(self, format_name: str = "json") -> str:
        """Export records in the specified format."""
        records = self.get_records()
        if format_name == "json":
            return self._json_export(records)
        elif format_name == "csv":
            return self._csv_export(records)
        elif format_name == "markdown":
            return self._markdown_export(records)
        return self._json_export(records)

    def _json_export(self, records: List[MetricsRecord]) -> str:
        import json

        return json.dumps([r.to_dict() for r in records], indent=2)

    def _csv_export(self, records: List[MetricsRecord]) -> str:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        if records:
            writer.writerow(["timestamp", "type", "metrics"])
            for r in records:
                writer.writerow([r.timestamp.isoformat(), r.type, r.metrics])
        return output.getvalue()

    def _markdown_export(self, records: List[MetricsRecord]) -> str:
        markdown = "# Metrics Export\n\n"
        markdown += f"- Records: {len(records)}\n"
        markdown += f"- Type: {records[0].type if records else 'all'}\n"
        markdown += "\n---\n\n"
        markdown += self._json_export(records)
        return markdown


class MetricKeys:
    """Predefined metric key constants."""

    ANALYSIS_CONFIDENCE = "analysis_confidence"
    ANALYSIS_RISK_SCORE = "analysis_risk_score"
    ANALYSIS_PROCESSING_TIME = "analysis_processing_time"
    ANALYSIS_CLASSIFICATION = "analysis_classification"
    ANALYSIS_RISK_LEVEL = "analysis_risk_level"
    MODEL_CONFIDENCE = "model_confidence"
    MODEL_LATENCY = "model_latency"
    SYSTEM_CPU_USAGE = "system_cpu_usage"
    SYSTEM_MEMORY_USAGE = "system_memory_usage"


# Global metrics engine instance
_metrics_engine: Optional["MetricsEngine"] = None


def get_metrics_engine() -> "MetricsEngine":
    """Get the global metrics engine instance."""
    global _metrics_engine
    if _metrics_engine is None:
        _metrics_engine = MetricsEngine()
    return _metrics_engine


def record_metrics(metrics: Dict[str, Any], record_type: str):
    """Convenience function to record metrics."""
    engine = get_metrics_engine()
    engine.record(metrics, record_type)
