from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json


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
        counts = Counter(r.type for r in self.records)
        return dict(counts)

    def count_in_range(
        self, start: datetime, end: datetime
    ) -> int:
        return sum(
            1
            for r in self.records
            if start <= r.timestamp <= end
        )

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
        self._index: Dict[str, List[MetricsRecord]] = defaultdict(list)

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
        self._index[record_type].append(record)

        # Enforce retention policy
        if len(self._records) > self.config.max_history_entries:
            # Remove oldest record
            removed = self._records.pop(0)
            self._index[removed.type].remove(removed)

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
            return json.dumps([r.to_dict() for r in records], indent=2)
        elif format_name == "csv":
            # Simple CSV export
            if not records:
                return "timestamp,type,metrics\n"
            lines = ["timestamp,type,metrics"]
            for r in records:
                metrics_str = json.dumps(r.metrics)
                lines.append(f"{r.timestamp.isoformat()},{r.type},{metrics_str}")
            return "\n".join(lines)
        elif format_name == "markdown":
            markdown = "# Metrics Export\n\n"
            markdown += f"- Records: {len(records)}\n"
            markdown += f"- Type: {records[0].type if records else 'all'}\n"
            markdown += "\n---\n\n"
            markdown += json.dumps([r.to_dict() for r in records], indent=2)
            return markdown
        return json.dumps([r.to_dict() for r in records], indent=2)


# Predefined metric keys
class MetricKeys:
    """Predefined metric key constants."""

    # Analysis metrics
    ANALYSIS_CONFIDENCE = "analysis_confidence"
    ANALYSIS_RISK_SCORE = "analysis_risk_score"
    ANALYSIS_PROCESSING_TIME = "analysis_processing_time"
    ANALYSIS_CLASSIFICATION = "analysis_classification"
    ANALYSIS_RISK_LEVEL = "analysis_risk_level"

    # Model metrics
    MODEL_CONFIDENCE = "model_confidence"
    MODEL_LATENCY = "model_latency"
    MODEL_SUCCESS_RATE = "model_success_rate"
    MODEL_FAILURE_RATE = "model_failure_rate"

    # RAG metrics
    RAG_RETRIEVAL_CONFIDENCE = "rag_retrieval_confidence"
    RAG_AVERAGE_SIMILARITY = "rag_average_similarity"
    RAG_CONTEXT_SIZE = "rag_context_size"
    RAG_LATENCY = "rag_latency"

    # Decision metrics
    DECISION_CONFIDENCE_DISTRIBUTION = "decision_confidence_distribution"
    DECISION_RISK_DISTRIBUTION = "decision_risk_distribution"
    DECISION_EVIDENCE_AGREEMENT = "decision_evidence_agreement"
    DECISION_LLM_CONTRIBUTION = "decision_llm_contribution"
    DECISION_ML_CONTRIBUTION = "decision_ml_contribution"

    # System metrics
    SYSTEM_CPU_USAGE = "system_cpu_usage"
    SYSTEM_MEMORY_USAGE = "system_memory_usage"
    SYSTEM_DISK_USAGE = "system_disk_usage"
    SYSTEM_API_LATENCY = "system_api_latency"
    SYSTEM_REQUEST_THROUGHPUT = "system_request_throughput"
    SYSTEM_ERROR_COUNT = "system_error_count"


# Global metrics engine instance
_metrics_engine: Optional[MetricsEngine] = None


def get_metrics_engine() -> MetricsEngine:
    """Get the global metrics engine instance."""
    global _metrics_engine
    if _metrics_engine is None:
        _metrics_engine = MetricsEngine()
    return _metrics_engine


def record_metrics(metrics: Dict[str, Any], record_type: str):
    """Convenience function to record metrics."""
    engine = get_metrics_engine()
    engine.record(metrics, record_type)