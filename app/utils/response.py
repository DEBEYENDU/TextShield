"""Response formatter: consistent HTTP-style envelopes.

Used by services to build responses and by routes for error envelopes,
so every API payload follows the same shape conventions.
"""
from __future__ import annotations

from typing import Any


def success(data: Any = None, message: str = "", **extra: Any) -> dict:
    """Wrap a successful payload: {"success": True, "data": ..., ...}."""
    payload: dict[str, Any] = {"success": True, "data": data}
    if message:
        payload["message"] = message
    payload.update(extra)
    return payload


def error(message: str, code: str = "error", detail: Any = None) -> dict:
    """Wrap an error payload: {"success": False, "error": {...}}."""
    return {
        "success": False,
        "error": {"code": code, "message": message, "detail": detail},
    }
