from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class AnalysisHistory:
    """Tracks analysis runs and their results."""

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def add(self, record: Dict[str, Any]) -> None:
        self._records.append(record)

    def get_all(self) -> List[Dict[str, Any]]:
        return self._records

    def filter(self, **kwargs) -> List[Dict[str, Any]]:
        results = self._records
        for key, value in kwargs.items():
            results = [r for r in results if r.get(key) == value]
        return results


class HistoryService:
    """Service for history queries and statistics."""

    def __init__(self, history: AnalysisHistory):
        self.history = history

    def get_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        return [r for r in self.history._records if r.get("timestamp")]

    def statistics(self) -> Dict[str, Any]:
        records = self.history._records
        if not records:
            return {}
        return {
            "total_analyses": len(records),
            "ioc_type_distribution": {
                k: sum(1 for r in records if r.get("ioc_type") == k)
                for k in ["url", "domain", "ip", "email", "hash"]
            },
            "severity_distribution": {
                k: sum(1 for r in records if r.get("severity") == k)
                for k in ["Low", "Medium", "High", "Critical"]
            },
        }


def get_dashboard_history(
    page: int = 1,
    page_size: int = 50,
    ioc_type: Optional[str] = None,
    provider: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return a paged, filterable threat history.

    In production this would query the database / cache.
    """
    # Mock data
    base = datetime.now(timezone.utc)
    all_entries = []
    for i in range(200):
        entry = {
            "id": i,
            "ioc_value": f"http://example{i % 50}.com",
            "ioc_type": ["url", "domain", "ip", "email", "hash"][i % 5],
            "threat_score": round(0.1 + (i % 20) * 0.04, 2),
            "provider": ["google_safe_browsing", "virustotal", "openphish", "phishtank", "urlhaus"][i % 5],
            "severity": ["Low", "Medium", "High", "Critical"][i % 4],
            "timestamp": (base - __import__("datetime").timedelta(hours=i * 2)).isoformat(),
        }
        all_entries.append(entry)

    # Apply filters
    filtered = all_entries
    if ioc_type:
        filtered = [e for e in filtered if e["ioc_type"] == ioc_type]
    if provider:
        filtered = [e for e in filtered if e["provider"] == provider]
    if severity:
        filtered = [e for e in filtered if e["severity"] == severity]
    if start_date:
        from datetime import datetime as _dt
        start_ts = start_date.timestamp()
        filtered = [e for e in filtered if _dt.fromisoformat(e["timestamp"]).timestamp() >= start_ts]
    if end_date:
        from datetime import datetime as _dt
        end_ts = end_date.timestamp()
        filtered = [e for e in filtered if _dt.fromisoformat(e["timestamp"]).timestamp() <= end_ts]

    # Pagination
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = filtered[start:end]

    return {
        "entries": page_entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def get_severity_distribution(entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Return severity distribution from a list of history entries."""
    if entries is None:
        entries = get_dashboard_history()["entries"]
    counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for e in entries:
        counts[e.get("severity", "Low")] = counts.get(e.get("severity", "Low"), 0) + 1
    total = sum(counts.values())
    return {
        "distribution": counts,
        "percentages": {k: (v / total * 100) if total else 0 for k, v in counts.items()},
        "total": total,
    }