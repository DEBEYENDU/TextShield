from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json


class AnalysisHistory:
    """Manages the history of completed analyses."""

    def __init__(self, max_entries: int = 10000, retention_days: int = 365):
        self.max_entries = max_entries
        self.retention_days = retention_days
        self._records: List[Dict[str, Any]] = []
        self._indexed: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._created_at = datetime.utcnow()

    def add(
        self,
        analysis_data: Dict[str, Any],
        record_type: str = "analysis",
    ) -> Optional[int]:
        """Add a new analysis to history."""
        # Enforce max entries
        if len(self._records) >= self.max_entries:
            # Remove oldest
            oldest = self._records.pop(0)
            # Remove from indexes
            for key in self._indexed:
                if oldest.get("type") in key or oldest.get("classification") in key:
                    self._indexed[key].remove(oldest)

        # Add timestamp if not present
        if "timestamp" not in analysis_data:
            analysis_data["timestamp"] = datetime.utcnow().isoformat()

        # Enforce retention
        timestamp = datetime.fromisoformat(
            analysis_data.get("timestamp", datetime.utcnow().isoformat())
        )
        retention_cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        if timestamp < retention_cutoff:
            return None

        # Add to records
        self._records.append(analysis_data)
        record_id = len(self._records) - 1

        # Index by common fields
        self._indexed["type"].append(analysis_data)
        if "classification" in analysis_data:
            self._indexed["classification"].append(analysis_data)
        if "message_type" in analysis_data:
            self._indexed["message_type"].append(analysis_data)
        if "risk_level" in analysis_data:
            self._indexed["risk_level"].append(analysis_data)

        return record_id

    def get(
        self,
        record_id: Optional[int] = None,
        message_type: Optional[str] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get records with filtering and pagination."""
        records = self._records

        # Filter by record_id
        if record_id is not None and 0 <= record_id < len(records):
            return [records[record_id]]

        # Filter by message_type
        if message_type:
            records = [r for r in records if r.get("message_type") == message_type]

        # Filter by classification
        if classification:
            records = [r for r in records if r.get("classification") == classification]

        # Filter by risk_level
        if risk_level:
            records = [r for r in records if r.get("risk_level") == risk_level]

        # Filter by date range
        if start_date or end_date:
            start = datetime.fromisoformat(start_date) if start_date else datetime.min
            end = datetime.fromisoformat(end_date) if end_date else datetime.max
            records = [
                r for r in records
                if start <= datetime.fromisoformat(r.get("timestamp", "1970-01-01"))
                <= end
            ]

        # Apply pagination
        records = records[skip:]
        if limit is not None:
            records = records[:limit]

        return records

    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search records by query string."""
        if fields is None:
            fields = ["classification", "message_type", "risk_level", "content"]

        results = []
        query_lower = query.lower()
        for r in self._records:
            match = any(
                query_lower in str(r.get(field, "")).lower()
                for field in fields
            )
            if match:
                results.append(r)

        return results

    def count(self, **filters) -> int:
        """Count records matching filters."""
        records = self._records
        for key, value in filters.items():
            records = [r for r in records if r.get(key) == value]
        return len(records)

    def export(self, format_name: str = "json") -> str:
        """Export history in specified format."""
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
    """Service interface for history operations."""

    @staticmethod
    def delete_older_than(days: int) -> int:
        """Delete records older than specified days. Returns count deleted."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(HistoryService._history._records)
        HistoryService._history._records = [
            r for r in HistoryService._history._records
            if datetime.fromisoformat(r.get("timestamp", "1970-01-01")) >= cutoff
        ]
        return original_count - len(HistoryService._history._records)

    @staticmethod
    def clear() -> int:
        """Clear all history. Returns count deleted."""
        original_count = len(HistoryService._history._records)
        HistoryService._history._records = []
        return original_count


# Global history instance
_history: Optional[AnalysisHistory] = None


def get_history() -> AnalysisHistory:
    """Get the global history instance."""
    global _history
    if _history is None:
        _history = AnalysisHistory()
    return _history