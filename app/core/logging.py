"""Structured application logging.

Design rules (PRD privacy requirements):
* Sensitive user message content is NEVER logged - only hashes, truncated
  previews and metadata.
* API keys and configuration secrets are never logged.
* Log lines are machine-parseable: timestamp | level | logger | message,
  with optional ``extra`` fields for structured context (e.g. request id).

The request-id contextvar lets any module attach the current request id
to its log output without threading it through every call.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.settings import BASE_DIR

_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(textshield_request_id)s | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    """Attach the current request id (from the contextvar) to records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.textshield_request_id = _request_id_var.get()
        return True


def set_request_id(request_id: str | None = None) -> str:
    """Set the request id for the current context; returns the id."""
    rid = request_id or uuid.uuid4().hex[:12]
    _request_id_var.set(rid)
    return rid


def clear_request_id() -> None:
    _request_id_var.set("-")


def setup_logging(level: int = logging.INFO, log_dir: Path | None = None) -> None:
    """Configure the root logger: console + rotating file, request-id filter."""
    root = logging.getLogger()
    if getattr(root, "_textshield_configured", False):
        return
    root.setLevel(level)

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)
    rid_filter = _RequestIdFilter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(rid_filter)
    root.addHandler(console)

    directory = log_dir or (BASE_DIR / "logs")
    directory.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        directory / "textshield.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(rid_filter)
    root.addHandler(file_handler)

    root._textshield_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
