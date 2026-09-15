"""Evaluation benchmark for semantic engine."""

from __future__ import annotations
from typing import List, Dict
from app.semantic.semantic_pipeline import SemanticPipeline


class SemanticBenchmark:
    def __init__(self):
        self.pipeline = SemanticPipeline()

    def run(self, samples: List[str]) -> Dict:
        results = []
        for s in samples:
            res = self.pipeline.analyze(message=s, include_embeddings=False)
            results.append({
                "language": res.language,
                "contexts": [c.domain for c in res.contexts],
                "topics": [t.topic for t in res.topics],
            })
        return {"samples": len(samples), "results": results}
