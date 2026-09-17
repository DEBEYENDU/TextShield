"""Privacy controls for attribution."""

from __future__ import annotations
import hashlib
from .config import config


def hash_identifier(value: str) -> str:
    if not config.privacy_hash:
        return value
    return hashlib.sha256(value.encode()).hexdigest()


def redact_pii(text: str) -> str:
    # simple redaction placeholder
    return text
