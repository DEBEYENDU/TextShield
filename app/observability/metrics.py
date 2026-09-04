"""Prometheus-style metrics & performance counters for RFC-011 Part 4."""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from typing import Dict

_counters: Counter[str] = Counter()
_histograms: Dict[str, list[float]] = defaultdict(list)


def incr(name: str, value: int = 1) -> None:
    _counters[name] += value


def observe(name: str, value: float) -> None:
    _histograms[name].append(value)
    # keep last 1000
    if len(_histograms[name]) > 1000:
        _histograms[name] = _histograms[name][-1000:]


def get_metrics() -> Dict[str, object]:
    out: Dict[str, object] = {"counters": dict(_counters)}
    hist = {}
    for k, vals in _histograms.items():
        if vals:
            hist[k] = {
                "count": len(vals),
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
                "p95": sorted(vals)[int(len(vals) * 0.95)] if len(vals) > 1 else vals[0],
            }
    out["histograms"] = hist
    out["uptime_seconds"] = time.time() - _start
    return out


_start = time.time()
