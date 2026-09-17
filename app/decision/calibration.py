"""Confidence calibration: map raw confidence to empirical accuracy.

Uses isotonic binning learned from evaluation run records when available;
falls back to a static near-identity mapping. Also exposes ECE so the
evaluation framework can report calibration quality of decisions.
"""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_BINS = [(0.0, 0.05), (0.5, 0.5), (0.7, 0.68), (0.85, 0.83),
                 (0.95, 0.93), (1.01, 0.97)]


class Calibrator:
    """Bin-based calibrator learned from labeled run records."""

    def __init__(self, bins: list[tuple[float, float]] | None = None):
        self.bins = sorted(bins or list(_DEFAULT_BINS))

    @classmethod
    def from_run_records(cls, records: list[dict], n_bins: int = 5) -> "Calibrator":
        """Learn P(correct | confidence-bin) from evaluation records."""
        buckets: list[list[float]] = [[] for _ in range(n_bins)]
        for record in records:
            conf = float(record.get("confidence", 0.0) or 0.0)
            idx = min(int(conf * n_bins), n_bins - 1)
            buckets[idx].append(1.0 if record.get("expected") == record.get("predicted") else 0.0)
        bins: list[tuple[float, float]] = []
        for i, bucket in enumerate(buckets):
            edge = (i + 1) / n_bins
            acc = sum(bucket) / len(bucket) if bucket else edge - 0.5 / n_bins
            bins.append((edge, round(min(max(acc, 0.01), 0.99), 3)))
        # enforce monotonicity (isotonic)
        for i in range(1, len(bins)):
            if bins[i][1] < bins[i - 1][1]:
                bins[i] = (bins[i][0], bins[i - 1][1])
        return cls(bins)

    @classmethod
    def from_latest_run(cls, runs_dir: str | Path = "data/eval/runs") -> "Calibrator":
        try:
            files = sorted(Path(runs_dir).glob("*.json"))
            if not files:
                return cls()
            run = json.loads(files[-1].read_text(encoding="utf-8"))
            return cls.from_run_records(run.get("records", []))
        except Exception:
            return cls()

    def calibrate(self, confidence: float) -> float:
        for edge, acc in self.bins:
            if confidence < edge:
                return acc
        return self.bins[-1][1] if self.bins else round(confidence, 3)

    def expected_calibration_error(self, records: list[dict]) -> float:
        total = 0.0
        n = len(records) or 1
        for record in records:
            conf = float(record.get("confidence", 0.0) or 0.0)
            correct = 1.0 if record.get("expected") == record.get("predicted") else 0.0
            total += abs(self.calibrate(conf) - correct)
        return round(total / n, 4)

    def to_dict(self) -> dict:
        return {"bins": self.bins}


calibrator = Calibrator()
