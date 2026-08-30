from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class AnalysisHistory:
    """Manages the history of completed analyses."""

    def __init__(self, max_entries: int = 10000, retention_days: int = 365):
        self.max_entries = max_entries
        self.retention_days = retention_days
        self._records: List[Dict[str, Any]] = []

    def add(
        self, analysis_data: Dict[str, Any], record_type: str = "analysis"
    ) -> Optional[int]:
        """Add a new analysis to history."""
        if len(self._records) >= self.max_entries:
            self._records.pop(0)

        if "timestamp" not in analysis_data:
            from datetime import datetime

            analysis_data["timestamp"] = datetime.utcnow().isoformat()

        # Enforce retention
        timestamp = datetime.fromisoformat(
            analysis_data.get("timestamp", datetime.utcnow().isoformat())
        )
        from datetime import datetime as dt_module

        retention_cutoff = dt_module.utcnow() - timedelta(days=self.retention_days)
        if timestamp < retention_cutoff:
            return None

        self._records.append(analysis_data)
        record_id = len(self._records) - 1
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
        original_count = (
            len(AnalysisHistory._records) if AnalysisHistory._records else 0
        )
        AnalysisHistory._records = [
            r
            for r in AnalysisHistory._records
            if datetime.fromisoformat(r.get("timestamp", "1970-01-01")) >= cutoff
        ]
        return original_count - len(AnalysisHistory._records)

    @staticmethod
    def clear() -> int:
        original_count = (
            len(AnalysisHistory._records) if AnalysisHistory._records else 0
        )
        AnalysisHistory._records = []
        return original_count


_history: Optional["AnalysisHistory"] = None


def get_history() -> "AnalysisHistory":
    global _history
    if _history is None:
        _history = AnalysisHistory()
    return _history
