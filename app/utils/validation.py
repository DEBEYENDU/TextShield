"""Validation utilities shared by schemas and services."""
from __future__ import annotations


def ensure_length(value: str | None, max_length: int) -> bool:
    """True when the value fits the length bound (None allowed)."""
    return value is None or len(value) <= max_length


def has_content(*values: str | None) -> bool:
    """True when at least one value has non-whitespace content."""
    return any((v or "").strip() for v in values)


def is_within_bounds(value: float, low: float, high: float) -> bool:
    return low <= value <= high
