"""Semantic intelligence configuration for RFC-011.

Centralizes transformer, multilingual, embedding, language detection,
normalization, and classifier settings. Falls back to existing settings
when environment variables are not provided.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from app.core.settings import settings


class EmbeddingConfig(BaseModel):
    model_name: str = Field(default_factory=lambda: settings.SEMANTIC_EMBEDDING_MODEL)
    dimension: int = Field(default_factory=lambda: settings.SEMANTIC_EMBEDDING_DIMENSION)
    cache_size: int = Field(default_factory=lambda: settings.SEMANTIC_CACHE_SIZE)
    batch_size: int = Field(default_factory=lambda: settings.SEMANTIC_BATCH_SIZE)
    device: str = Field(default_factory=lambda: settings.SEMANTIC_DEVICE)


class TransformerConfig(BaseModel):
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    max_seq_length: int = 512
    truncation: bool = True
    normalize_embeddings: bool = True
    device: str = "auto"


class LanguageConfig(BaseModel):
    detection_mode: str = "transformer"
    script_fallback: bool = True
    supported_languages: list[str] = ["en", "hi", "bn", "ta", "te", "mr", "kn", "gu", "pa", "ur", "ar"]
    min_text_len: int = 5
    confidence_threshold: float = 0.45


class NormalizationConfig(BaseModel):
    unicode_normalize: bool = True
    emoji_preserve: bool = True
    smart_chars: bool = True
    whitespace_collapse: bool = True
    lower_case_for_matching: bool = True


class SimilarityConfig(BaseModel):
    metric: str = "cosine"
    threshold_similar: float = 0.75
    threshold_near: float = 0.55


class ContextConfig(BaseModel):
    use_transformer_logits: bool = True
    lexicon_fallback: bool = True
    max_contexts: int = 4
    confidence_boost: float = 0.12


class MultilingualConfig(BaseModel):
    enable_hinglish: bool = True
    enable_transliteration: bool = True
    transliteration_model: str = "indic_transliteration"
    language_specific_normalization: bool = True


class SemanticIntelligenceConfig(BaseModel):
    enabled: bool = True
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    transformer: TransformerConfig = Field(default_factory=TransformerConfig)
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    similarity: SimilarityConfig = Field(default_factory=SimilarityConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    multilingual: MultilingualConfig = Field(default_factory=MultilingualConfig)


config = SemanticIntelligenceConfig()
