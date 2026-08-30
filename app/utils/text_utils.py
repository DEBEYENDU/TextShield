"""Text utilities: safe truncation, hashing, redaction helpers."""

from __future__ import annotations

import hashlib
import re

_SENSITIVE_PATTERN = re.compile(r"[^\s]+")

ELLIPSIS = "..."


def sha256(text: str) -> str:
    """Deterministic SHA-256 hex digest of a string."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def truncate(text: str | None, limit: int, ellipsis: str = ELLIPSIS) -> str:
    """Truncate text to ``limit`` characters, keeping whole words."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - len(ellipsis)]
    return cut.rsplit(" ", 1)[0].rstrip() + ellipsis


def mask_secret(value: str | None, visible: int = 4) -> str:
    """Mask a secret for display: keep the tail, replace the head with *."""
    if not value:
        return ""
    if len(value) <= visible + 2:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def slugify(value: str) -> str:
    """Lowercase, space/dash -> underscore, drop non-alphanumeric."""
    value = re.sub(r"[\s\-/]+", "_", value.strip().lower())
    value = re.sub(r"[^a-z0-9_]", "", value)
    return value.strip("_")
