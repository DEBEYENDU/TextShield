"""Privacy protection."""

from __future__ import annotations

import hashlib
import re

def sanitize_message(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def redact_secrets(text: str) -> str:
    return re.sub(r"(api[_-]?key\s*[=:]\s*)[^\s&]+", r"\1***", text, flags=re.I)
