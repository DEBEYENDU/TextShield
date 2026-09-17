"""Hinglish detection and handling.

Detects romanized Hindi mixed with English and provides normalization helpers.
"""

from __future__ import annotations
import re

_HINGLISH_WORDS = {
    "hai", "ho", "kya", "kyu", "kaise", "kab", "kahaan", "kaun", "mein", "par", "se",
    "ko", "ke", "ka", "ki", "aur", "yah", "yeh", "usse", "mujhe", "aap", "hum", "tum",
}

_HINGLISH_RE = re.compile(r'\b(' + '|'.join(_HINGLISH_WORDS) + r')\b', re.IGNORECASE)


def is_hinglish(text: str) -> bool:
    if not text:
        return False
    matches = _HINGLISH_RE.findall(text)
    words = text.split()
    if not words:
        return False
    ratio = len(matches) / len(words)
    return ratio >= 0.15


def normalize_hinglish(text: str) -> str:
    if not is_hinglish(text):
        return text
    text = re.sub(r'\bhai\b', 'is', text, flags=re.IGNORECASE)
    return text
