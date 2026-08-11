"""Data models for the SQLite persistence layer.

The on-disk schema is managed by ``database.py``; this module holds the
plain Python dataclass used to construct history records.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalysisRecord:
    timestamp: str
    input_type: str
    message_hash: str
    classification: str
    confidence: float
    risk_level: str
    preview: str | None = None