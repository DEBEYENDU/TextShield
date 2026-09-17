"""Hybrid semantic + lexicon integration.

Combines transformer scores with lexicon-based signals for robust detection.
"""

from __future__ import annotations
from app.semantic.classifier import TransformerClassifier
from app.semantic.semantic_pipeline import SemanticPipeline


class HybridSemanticEngine:
    def __init__(self):
        self.classifier = TransformerClassifier()
        self.pipeline = SemanticPipeline()

    def analyze(self, text: str, message_type: str = "text"):
        semantic = self.pipeline.analyze(message=text, message_type=message_type, include_embeddings=True)
        transformer_scores = self.classifier.classify(text)
        features = semantic.semantic_features
        return {
            "semantic": semantic,
            "transformer_scores": transformer_scores,
            "features": features,
        }
