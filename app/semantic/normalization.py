"""Advanced text normalization for multilingual inputs.

Builds on semantic_utils preprocessing with language-aware normalization,
emoji preservation, and Hinglish handling.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.semantic.config import config
from app.semantic.semantic_utils import preprocess_text as base_preprocess
from app.semantic.semantic_utils import normalize_unicode, clean_whitespace, normalize_special_characters

logger = get_logger(__name__)


def normalize_text(text: str, language: str | None = None) -> str:
    if not text:
        return ""
    if config.normalization.unicode_normalize:
        text = normalize_unicode(text)
    if config.normalization.smart_chars:
        text = normalize_special_characters(text)
    if config.normalization.whitespace_collapse:
        text = clean_whitespace(text)
    if config.multilingual.language_specific_normalization and language:
        text = _language_specific_normalize(text, language)
    return text


def _language_specific_normalize(text: str, language: str) -> str:
    if language in {"hi", "mr", "bn", "ta", "te"}:
        text = _normalize_indic(text)
    if language in {"ar", "ur", "fa"}:
        text = _normalize_arabic_script(text)
    return text


def _normalize_indic(text: str) -> str:
    normalized = text.replace("्र", "र").replace("्य", "य")
    normalized = normalized.replace("…", "...")
    return normalized


def _normalize_arabic_script(text: str) -> str:
    replacements = {
        "\u0640": "",
        "\u061f": "?",
        "\u066b": ".",
        "\u066c": ",",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def normalize_for_matching(text: str) -> str:
    normalized = normalize_text(text)
    if config.normalization.lower_case_for_matching:
        normalized = normalized.lower()
    return normalized
