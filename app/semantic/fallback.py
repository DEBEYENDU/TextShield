"""Fallback strategy for semantic pipeline."""

from __future__ import annotations

from app.semantic.semantic_pipeline import SemanticPipeline


class SemanticFallback:
    def __init__(self):
        self.pipeline = SemanticPipeline()

    def analyze_safe(self, text: str, message_type: str = "text"):
        try:
            return self.pipeline.analyze(message=text, message_type=message_type, include_embeddings=False)
        except Exception:
            from app.semantic.semantic_models import SemanticAnalysisResult, SemanticContext, SemanticFeatures, SemanticConfidence
            return SemanticAnalysisResult(
                language="unknown",
                contexts=[SemanticContext(domain="unknown", confidence=0.0)],
                topics=[],
                entities=[],
                embedding_dimension=0,
                embeddings={},
                semantic_features=SemanticFeatures(
                    message_length=0,
                    word_count=0,
                    sentence_count=0,
                    question_count=0,
                    imperative_count=0,
                    emoji_count=0,
                    url_count=0,
                    email_count=0,
                    phone_count=0,
                    money_count=0,
                    date_count=0,
                    time_count=0,
                    has_request=False,
                    has_offer=False,
                    has_urgency=False,
                    has_financial_reference=False,
                    has_credential_request=False,
                    has_personal_information_request=False,
                ),
                confidence=SemanticConfidence(language=0.0, context=0.0, topic=0.0, entity=0.0),
                sentences=[],
                embedding_provider="fallback",
                normalized_text="",
                message_preview="",
            )
