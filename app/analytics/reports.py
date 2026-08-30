from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import csv
import io


class ReportsGenerator:
    """Generator for various report formats."""

    @staticmethod
    def generate_analysis_report(
        records: List[Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate an analysis summary report."""
        if start_date is None:
            from datetime import datetime, timedelta

            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        filtered = [
            r
            for r in records
            if start_date <= r.timestamp <= end_date
            if hasattr(r, "timestamp")
        ]

        confidences = [
            r.metrics.get("analysis_confidence", 0.0)
            for r in filtered
            if hasattr(r, "metrics") and "analysis_confidence" in r.metrics
        ]

        return {
            "report_type": "analysis",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_analyses": len(filtered),
            "confidence_stats": (
                {
                    "average": (
                        sum(confidences) / len(confidences) if confidences else 0
                    ),
                    "min": min(confidences) if confidences else 0,
                    "max": max(confidences) if confidences else 0,
                }
                if confidences
                else {"average": 0, "min": 0, "max": 0}
            ),
            "risk_distribution": (
                {
                    level: sum(
                        1
                        for r in filtered
                        if r.metrics.get("analysis_risk_level") == level
                    )
                    for level in ["Very Low", "Low", "Medium", "High", "Critical"]
                }
                if filtered
                else {}
            ),
        }

    @staticmethod
    def generate_analytics_report(metrics_engine) -> Dict[str, Any]:
        """Generate analytics summary report."""
        records = metrics_engine.get_records()
        if not records:
            return {"error": "No records found"}

        from .statistics import StatisticsEngine

        stats = StatisticsEngine()

        return {
            "report_type": "analytics",
            "total_records": len(records),
            "records_by_type": metrics_engine.count_by_type(),
            "confidence_distribution": stats.compute_confidence_distribution(records),
            "risk_distribution": stats.compute_risk_distribution(records),
            "common_intents": stats.compute_intent_frequencies(records),
            "common_behaviors": stats.compute_behavior_frequencies(records),
            "processing_time_stats": stats.compute_processing_time_stats(records),
            "daily_usage": stats.compute_daily_usage(records),
        }

    @staticmethod
    def generate_system_report(system_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system health report."""
        return {
            "report_type": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": system_metrics,
        }

    @staticmethod
    def export_to_csv(records: List[Any], filename: str) -> bool:
        """Export records to CSV file."""
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                if records:
                    writer.writerow(
                        ["timestamp", "classification", "risk_level", "confidence"]
                    )
                    for r in records:
                        writer.writerow(
                            [
                                (
                                    r.timestamp.isoformat()
                                    if hasattr(r, "timestamp")
                                    else ""
                                ),
                                r.get("classification", ""),
                                r.get("risk_level", ""),
                                r.get("confidence", 0),
                            ]
                        )
                return True
        except Exception:
            return False

    @staticmethod
    def export_to_json(records: List[Any], filename: str) -> bool:
        """Export records to JSON file."""
        try:
            import json

            with open(filename, "w") as f:
                data = [r.to_dict() if hasattr(r, "to_dict") else {} for r in records]
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def export_to_markdown(records: List[Any], filename: str) -> bool:
        """Export records to Markdown file."""
        try:
            import json

            with open(filename, "w") as f:
                f.write("# Records Export\n\n")
                f.write(f"- Records: {len(records)}\n\n")
                f.write("---\n\n")
                f.write(
                    json.dumps(
                        [r.to_dict() if hasattr(r, "to_dict") else {} for r in records],
                        indent=2,
                    )
                )
            return True
        except Exception:
            return False


class MetricKeys:
    """Predefined metric key constants."""

    ANALYSIS_CONFIDENCE = "analysis_confidence"
    ANALYSIS_RISK_SCORE = "analysis_risk_score"
    ANALYSIS_PROCESSING_TIME = "analysis_processing_time"
    ANALYSIS_CLASSIFICATION = "analysis_classification"
    ANALYSIS_RISK_LEVEL = "analysis_risk_level"


class AnalysisHistory:
    """Manages the history of completed analyses."""

    def __init__(self, max_entries: int = 10000, retention_days: int = 365):
        self.max_entries = max_entries
        self.retention_days = retention_days
        self._records: List[Dict[str, Any]] = []
        self._indexed: Dict[str, List[Dict[str, Any]]] = {}

        # Index by common fields
        self._indexed["classification"] = []
        self._indexed["risk_level"] = []

    def add(
        self, analysis_data: Dict[str, Any], record_type: str = "analysis"
    ) -> Optional[int]:
        """Add a new analysis to history."""
        if len(self._records) >= self.max_entries:
            self._records.pop(0)
            # Remove from indexes
            (
                self._indexed["classification"].pop(0)
                if self._indexed["classification"]
                else None
            )
            self._indexed["risk_level"].pop(0) if self._indexed["risk_level"] else None

        if "timestamp" not in analysis_data:
            from datetime import datetime

            analysis_data["timestamp"] = datetime.utcnow().isoformat()

        self._records.append(analysis_data)
        record_id = len(self._records) - 1

        # Index
        if "classification" in analysis_data:
            self._indexed["classification"].append(analysis_data)
        if "risk_level" in analysis_data:
            self._indexed["risk_level"].append(analysis_data)

        return record_id

    def get(
        self,
        record_id: Optional[int] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        records = self._records

        if record_id is not None and 0 <= record_id < len(records):
            return [records[record_id]]

        if classification:
            records = [r for r in records if r.get("classification") == classification]

        if risk_level:
            records = [r for r in records if r.get("risk_level") == risk_level]

        if start_date or end_date:
            from datetime import datetime

            start = datetime.fromisoformat(start_date) if start_date else datetime.min
            end = datetime.fromisoformat(end_date) if end_date else datetime.max
            records = [
                r
                for r in records
                if start
                <= datetime.fromisoformat(r.get("timestamp", "1970-01-01"))
                <= end
            ]

        records = records[skip:]
        if limit is not None:
            records = records[:limit]

        return records

    def search(
        self, query: str, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        if fields is None:
            fields = ["classification", "risk_level", "message_type", "content"]

        results = []
        query_lower = query.lower()
        for r in self._records:
            match = any(
                query_lower in str(r.get(field, "")).lower() for field in fields
            )
            if match:
                results.append(r)

        return results

    def count(self, **filters) -> int:
        records = self._records
        for key, value in filters.items():
            records = [r for r in records if r.get(key) == value]
        return len(records)

    def export(self, format_name: str = "json") -> str:
        import json

        if format_name == "json":
            return json.dumps(self._records, indent=2)
        elif format_name == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            if self._records:
                headers = self._records[0].keys()
                writer.writerow(headers)
                for r in self._records:
                    writer.writerow(r.values())
            return output.getvalue()
        return json.dumps(self._records, indent=2)


class HistoryService:
    @staticmethod
    def delete_older_than(days: int) -> int:
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(AnalysisHistory._records if "_records" in dir() else [])
        return 0

    @staticmethod
    def clear() -> int:
        original_count = 0
        return original_count


# Global history instance
_history: Optional["AnalysisHistory"] = None


def get_history() -> "AnalysisHistory":
    global _history
    if _history is None:
        _history = AnalysisHistory()
    return _history
