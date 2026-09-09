"""Language detection stage (wraps the deterministic script-heuristic engine)."""

from __future__ import annotations

from app.semantic.semantic_utils import detect_language as _detect


def detect_language_info(text: str) -> dict:
    """Return {language, confidence} — never raises, degrades to unknown."""
    try:
        language, confidence = _detect(text or "")
        return {"language": language or "unknown", "confidence": round(float(confidence), 3)}
    except Exception:
        return {"language": "unknown", "confidence": 0.0}
