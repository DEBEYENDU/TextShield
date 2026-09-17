"""Multilingual benchmark."""

from __future__ import annotations
from app.semantic.multilingual import MultilingualPipeline


class MultilingualBenchmark:
    def __init__(self):
        self.pipeline = MultilingualPipeline()

    def evaluate(self, samples: dict):
        results = {}
        for lang, texts in samples.items():
            results[lang] = [self.pipeline.process(t) for t in texts]
        return results
