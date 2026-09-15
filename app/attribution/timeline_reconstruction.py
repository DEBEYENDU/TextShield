"""Timeline and campaign reconstruction."""

from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timedelta
from .config import config
from app.core.logging import get_logger

logger = get_logger(__name__)


class TimelineReconstructor:
    def __init__(self):
        self._events: List[Dict] = []

    def add_event(self, message_id: str, timestamp: datetime, ioc_type: str, ioc_value: str):
        self._events.append({
            "message_id": message_id,
            "timestamp": timestamp,
            "ioc_type": ioc_type,
            "ioc_value": ioc_value
        })

    def reconstruct(self, window_days: int | None = None) -> List[Dict]:
        days = window_days or config.temporal_window_days
        cutoff = datetime.utcnow() - timedelta(days=days)
        events = [e for e in self._events if e["timestamp"] >= cutoff]
        # group by ioc_value
        grouped: Dict[str, List[Dict]] = {}
        for e in events:
            key = e["ioc_value"]
            grouped.setdefault(key, []).append(e)
        timeline = []
        for ioc, evs in grouped.items():
            evs_sorted = sorted(evs, key=lambda x: x["timestamp"])
            timeline.append({
                "ioc": ioc,
                "first_seen": evs_sorted[0]["timestamp"],
                "last_seen": evs_sorted[-1]["timestamp"],
                "count": len(evs_sorted),
                "messages": [e["message_id"] for e in evs_sorted]
            })
        logger.debug("Timeline reconstructed with %d IOC groups", len(timeline))
        return timeline
