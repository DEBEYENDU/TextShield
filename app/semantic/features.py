"""Semantic feature extraction with multilingual awareness.

Wraps pipeline.compute_features with additional transformer-derived features.
"""

from __future__ import annotations

from app.semantic.semantic_pipeline import SemanticPipeline
from app.semantic.semantic_models import SemanticFeatures
from app.semantic.semantic_utils import segment_sentences
from app.semantic.embeddings import MultilingualEmbeddingService


class SemanticFeaturesEngine:
    def __init__(self, pipeline: SemanticPipeline | None = None):
        self.pipeline = pipeline or SemanticPipeline()
        self.embedder = MultilingualEmbeddingService()

    def extract(self, text: str, language: str | None = None) -> SemanticFeatures:
        sentences = segment_sentences(text)
        from app.semantic.semantic_pipeline import SemanticPipeline as SP
        dummy_entities = []
        features = self.pipeline.compute_features(text, sentences, dummy_entities)
        return features
