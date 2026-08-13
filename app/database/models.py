"""Data models for the SQLite persistence layer.

The on-disk schema is managed by migrations (``app/database/
migrations.py``); this module holds the plain dataclass used to
construct history records.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AnalysisRecord:
    timestamp: str
    input_type: str
    message_hash: str
    classification: str
    confidence: float
    risk_level: str
    risk_score: float = 0.0
    intent: str | None = None
    message_type: str = "generic"
    message: str = ""
    preview: str | None = None

    def to_record_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "input_type": self.input_type,
            "message_hash": self.message_hash,
            "message": self.message,
            "classification": self.classification,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "intent": self.intent,
            "message_type": self.message_type,
            "preview": self.preview,
        }
