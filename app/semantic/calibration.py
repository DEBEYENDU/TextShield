"""Confidence calibration for semantic scores."""

from __future__ import annotations
import math


def calibrate_confidence(raw: float, temperature: float = 1.0) -> float:
    raw = max(0.0, min(1.0, raw))
    calibrated = 1.0 / (1.0 + math.exp(-(raw - 0.5) / max(0.01, temperature)))
    return round(calibrated, 3)


def calibrate_scores(scores: list[float]) -> list[float]:
    return [calibrate_confidence(s) for s in scores]
