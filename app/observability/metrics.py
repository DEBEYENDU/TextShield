"""Application metrics engine."""

from __future__ import annotations

import time
from threading import Lock
from typing import Dict

class MetricsEngine:
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, list[float]] = {}
        self._lock = Lock()

    def inc(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def observe(self, name: str, duration_ms: float) -> None:
        with self._lock:
            self._timers.setdefault(name, []).append(duration_ms)

    def get(self) -> dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timers": {k: {"count": len(v), "avg_ms": sum(v)/len(v) if v else 0} for k, v in self._timers.items()}
            }

metrics = MetricsEngine()
