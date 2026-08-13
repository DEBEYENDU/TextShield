"""Semantic service facade for TextShield.

Public entry point for the Semantic Understanding Engine. Exposes the
pipeline (``analyze_message`` / typed analyzers) and similarity utilities
(cosine similarity, embedding distance, sentence similarity) that later
phases (intent, decision, explainability) will consume.

This module is intentionally free of any classification/spam logic and of
any dependency on RAG, LLM reasoning or the Decision Engine.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from app.semantic.embedding_service import EmbeddingService, embedding_service
from app.semantic.semantic_models import SemanticAnalysisResult
from app.semantic.semantic_pipeline import SemanticPipeline


class SimilarityService:
    """Deterministic similarity helpers over raw or embedded text."""

    @staticmethod
    def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        """Cosine similarity in [0, 1] (0 for empty/zero vectors)."""
        a = list(vec_a)
        b = list(vec_b)
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return round(max(0.0, min(1.0, dot / (norm_a * norm_b))), 6)

    @staticmethod
    def embedding_distance(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        """Euclidean distance between two embedding vectors."""
        a = list(vec_a)
        b = list(vec_b)
        if not a or not b or len(a) != len(b):
            return float("inf")
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def sentence_similarity(
        self, text_a: str, text_b: str, embedding_service_: EmbeddingService | None = None
    ) -> float:
        """Cosine similarity between embeddings of two texts.

        Falls back to token-overlap (Jaccard) similarity if embeddings
        cannot be produced.
        """
        service = embedding_service_ or embedding_service
        try:
            vec_a = service.embed_one(text_a)
            vec_b = service.embed_one(text_b)
        except Exception:
            tokens_a = set(text_a.lower().split())
            tokens_b = set(text_b.lower().split())
            if not tokens_a and not tokens_b:
                return 1.0
            return round(
                len(tokens_a & tokens_b) / len(tokens_a | tokens_b), 6
            )
        return self.cosine_similarity(vec_a, vec_b)


class SemanticService:
    """Facade over the semantic pipeline for each supported input type."""

    def __init__(
        self,
        pipeline: SemanticPipeline | None = None,
        embedding: EmbeddingService | None = None,
        similarity: SimilarityService | None = None,
    ) -> None:
        self.pipeline = pipeline or SemanticPipeline()
        self.embedding = embedding or embedding_service
        self.similarity = similarity or SimilarityService()

    def analyze_message(
        self,
        message: str = "",
        *,
        message_type: str = "text",
        subject: str | None = None,
        sender: str | None = None,
        body: str | None = None,
        email_raw: str | None = None,
        include_embeddings: bool = True,
        **_: Any,
    ) -> SemanticAnalysisResult:
        """Analyze a single message of any supported type.

        ``message_type`` is one of ``text|sms|email|chat``. For emails the
        message body, subject and sender are taken from the provided fields
        or parsed out of ``email_raw``.
        """
        return self.pipeline.analyze(
            message=message,
            message_type=message_type,
            subject=subject,
            sender=sender,
            body=body,
            email_raw=email_raw,
            include_embeddings=include_embeddings,
        )

    def analyze_sms(self, message: str, *, include_embeddings: bool = True) -> SemanticAnalysisResult:
        return self.analyze_message(message, message_type="sms", include_embeddings=include_embeddings)

    def analyze_email(
        self,
        subject: str | None = None,
        sender: str | None = None,
        body: str | None = None,
        email_raw: str | None = None,
        *,
        include_embeddings: bool = True,
    ) -> SemanticAnalysisResult:
        return self.analyze_message(
            message=body or "",
            message_type="email",
            subject=subject,
            sender=sender,
            body=body,
            email_raw=email_raw,
            include_embeddings=include_embeddings,
        )

    def analyze_text(self, message: str, *, include_embeddings: bool = True) -> SemanticAnalysisResult:
        return self.analyze_message(message, message_type="text", include_embeddings=include_embeddings)

    def analyze_chat(self, message: str, *, include_embeddings: bool = True) -> SemanticAnalysisResult:
        return self.analyze_message(message, message_type="chat", include_embeddings=include_embeddings)

    def batch_analyze(
        self,
        messages: Sequence[tuple[str, str]],
        *,
        include_embeddings: bool = False,
    ) -> list[SemanticAnalysisResult]:
        """Analyze ``(message, message_type)`` pairs, embeddings disabled by
        default for throughput."""
        return [
            self.analyze_message(text, message_type=msg_type, include_embeddings=include_embeddings)
            for text, msg_type in messages
        ]


semantic_service = SemanticService()

__all__ = ["SemanticService", "SimilarityService", "semantic_service"]
