"""Multilingual pipeline orchestrator.

Coordinates language detection, normalization, hinglish handling, and
transliteration for semantic intelligence.
"""

from __future__ import annotations

from app.semantic.language import detect_language
from app.semantic.normalization import normalize_text
from app.semantic.hinglish import is_hinglish, normalize_hinglish
from app.semantic.transliteration import transliterate


class MultilingualPipeline:
    def process(self, text: str) -> dict:
        lang, conf = detect_language(text)
        normalized = normalize_text(text, lang)
        hinglish = is_hinglish(normalized)
        if hinglish:
            normalized = normalize_hinglish(normalized)
        result = {
            "original": text,
            "language": lang,
            "confidence": conf,
            "normalized": normalized,
            "is_hinglish": hinglish,
        }
        if lang in {"hi", "mr", "bn"}:
            try:
                result["transliterated"] = transliterate(normalized, source_script="devanagari", target_script="iast")
            except Exception:
                result["transliterated"] = None
        return result
