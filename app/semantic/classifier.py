"""Transformer-based semantic classifier.

Provides similarity-based classification with confidence calibration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.semantic.transformer import similarity_score
from app.semantic.config import config


@dataclass
class ClassificationResult:
    label: str
    confidence: float


class TransformerClassifier:
    def __init__(self, categories: dict[str, str] | None = None):
        self.categories = categories or {
            "legitimate": "official communication from known sender",
            "spam": "unsolicited promotional or scam message",
            "phishing": "attempt to steal credentials or personal data",
            "fraud": "deceptive financial request",
        }

    def classify(self, text: str) -> List[ClassificationResult]:
        scores = []
        for label, descriptor in self.categories.items():
            try:
                sim = similarity_score(text, descriptor)
                scores.append(ClassificationResult(label=label, confidence=round(sim, 3)))
            except Exception:
                continue
        scores.sort(key=lambda r: r.confidence, reverse=True)
        return scores[:3]
