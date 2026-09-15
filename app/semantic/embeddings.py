"""Transformer embedding abstraction with multilingual support.

Wraps existing EmbeddingService with language aware routing and
normalization for RFC-011.
"""

from __future__ import annotations

from typing import Sequence

from app.semantic.embedding_service import EmbeddingService, embedding_service
from app.semantic.config import config
from app.semantic.normalization import normalize_text


class MultilingualEmbeddingService:
    def __init__(self, service: EmbeddingService | None = None):
        self.service = service or embedding_service

    def embed(self, texts: Sequence[str], language: str | None = None) -> list[list[float]]:
        normalized = [normalize_text(t, language) for t in texts]
        return self.service.embed(normalized)

    def embed_one(self, text: str, language: str | None = None) -> list[float]:
        normalized = normalize_text(text, language)
        return self.service.embed_one(normalized)

    @property
    def dimension(self) -> int:
        return self.service.dimension

    @property
    def provider(self) -> str:
        return self.service.provider
