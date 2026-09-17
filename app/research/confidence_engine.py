"""Confidence scoring."""

from __future__ import annotations
from .models import Evidence

class ConfidenceEngine:
    def compute(self, evidence: Evidence) -> float:
        return evidence.reliability * evidence.freshness * evidence.confidence
