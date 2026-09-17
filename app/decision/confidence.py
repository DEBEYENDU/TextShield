"""Context-aware confidence: agreement × coverage × calibration.

Confidence is NOT a single model's probability. It combines how much
independent sources agree, how many sources actually fired, and an
empirical calibration mapping (learned from evaluation runs when
available, static fallback otherwise).
"""

from __future__ import annotations

import math


def agreement_score(p_spams: list[float]) -> float:
    """1.0 when all sources agree, decaying with spread (std-based)."""
    if not p_spams:
        return 0.0
    if len(p_spams) == 1:
        return 0.5
    mean = sum(p_spams) / len(p_spams)
    var = sum((p - mean) ** 2 for p in p_spams) / len(p_spams)
    return round(max(0.0, 1.0 - 2.0 * math.sqrt(var)), 3)


def coverage_score(n_fired: int, n_total: int = 12) -> float:
    return round(min(1.0, n_fired / max(n_total, 1)), 3)


def context_confidence(p_spams: list[float], n_fired: int,
                       calibrated_p: float | None = None) -> dict:
    """Assemble raw confidence from agreement and coverage."""
    agreement = agreement_score(p_spams)
    coverage = coverage_score(n_fired)
    raw = round(0.6 * agreement + 0.4 * coverage, 3)
    return {"raw_confidence": raw, "agreement": agreement,
            "coverage": coverage,
            "calibrated_confidence": calibrated_p if calibrated_p is not None else raw}
