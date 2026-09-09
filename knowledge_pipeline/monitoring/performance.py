"""Lightweight per-stage performance timers."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class StageTiming:
    name: str
    seconds: float = 0.0
    calls: int = 0


class PerformanceMonitor:
    def __init__(self):
        self._starts: dict[str, float] = {}
        self.stages: dict[str, StageTiming] = {}

    @contextmanager
    def stage(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            timing = self.stages.setdefault(name, StageTiming(name))
            timing.seconds = round(timing.seconds + elapsed, 4)
            timing.calls += 1

    def report(self) -> dict:
        total = sum(t.seconds for t in self.stages.values()) or 1e-9
        return {
            name: {"seconds": t.seconds, "calls": t.calls,
                   "share": round(t.seconds / total, 4)}
            for name, t in sorted(self.stages.items(), key=lambda kv: -kv[1].seconds)
        }
