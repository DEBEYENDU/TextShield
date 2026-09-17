"""Transliteration support for Indic scripts.

Provides lightweight transliteration fallback when external libraries are unavailable.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from indic_transliteration import sanscript
    _HAS_INDIC = True
except Exception:
    _HAS_INDIC = False


def transliterate(text: str, source_script: str = "devanagari", target_script: str = "iast") -> str:
    if not text:
        return ""
    if not _HAS_INDIC:
        logger.warning("indic_transliteration not available, returning original text")
        return text
    try:
        return sanscript.transliterate(text, sanscript.__dict__.get(source_script.upper(), sanscript.DEVANAGARI), sanscript.__dict__.get(target_script.upper(), sanscript.ITRANS))
    except Exception as exc:
        logger.warning("Transliteration failed: %s", exc)
        return text
