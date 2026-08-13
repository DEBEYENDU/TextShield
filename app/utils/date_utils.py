"""Date/time utilities: ISO-8601 UTC helpers."""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_now_iso(include_seconds: bool = True) -> str:
    """ISO-8601 UTC timestamp string, seconds precision by default."""
    return utc_now().isoformat(timespec="seconds" if include_seconds else "microseconds")


def utc_now_ms() -> int:
    """Unix epoch milliseconds."""
    return int(utc_now().timestamp() * 1000)


def parse_iso(value: str) -> datetime | None:
    """Best-effort parse of an ISO timestamp; None on failure."""
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
