"""Semantic similarity engine for multilingual comparison.

Combines transformer cosine similarity with lexical fallback.
"""

from __future__ import annotations

import math
from typing import Sequence

from app.semantic.config import config
from app.semantic.transformer import similarity_score as transformer_sim
from app.semantic.semantic_service import SimilarityService as BaseSimilarity


class SemanticSimilarity:
    def __init__(self):
        self.base = BaseSimilarity()

    def cosine(self, a: Sequence[float], b: Sequence[float]) -> float:
        return self.base.cosine_similarity(a, b)

    def sentence_similarity(self, a: str, b: str) -> float:
        try:
            score = transformer_sim(a, b)
            if score > 0:
                return round(score, 6)
        except Exception:
            pass
        return self.base.sentence_similarity(a, b)

    def is_similar(self, a: str, b: str) -> bool:
        score = self.sentence_similarity(a, b)
        return score >= config.similarity.threshold_similar

    def is_near(self, a: str, b: str) -> bool:
        score = self.sentence_similarity(a, b)
        return score >= config.similarity.threshold_near
