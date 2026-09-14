"""Structured logging with redaction."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[=:]\s*)[^\s&]+", re.I),
    re.compile(r"(bearer\s+)[^\s]+", re.I),
    re.compile(r"(password\s*[=:]\s*)[^\s&]+", re.I),
    re.compile(r"(token\s*[=:]\s*)[^\s&]+", re.I),
]

def redact_secrets(text: str) -> str:
    if not isinstance(text, str):
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(r"\1***REDACTED***", out)
    return out

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "request_id": getattr(record, "request_id", "-"),
            "analysis_id": getattr(record, "analysis_id", "-"),
        }
        msg = record.getMessage()
        data["msg"] = redact_secrets(msg)
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
