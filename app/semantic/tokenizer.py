"""Multilingual tokenizer utilities.

Provides sentence and word tokenization with language-aware segmentation.
"""

from __future__ import annotations

from app.semantic.semantic_utils import segment_sentences, preprocess_text, tokenize_words
from app.semantic.normalization import normalize_text


def tokenize(text: str, language: str | None = None) -> list[str]:
    normalized = normalize_text(text, language)
    if not normalized:
        return []
    return [t for t in normalized.split() if t]


def tokenize_sentences(text: str, language: str | None = None) -> list[str]:
    normalized = normalize_text(text, language)
    sentences = segment_sentences(normalized)
    return sentences
