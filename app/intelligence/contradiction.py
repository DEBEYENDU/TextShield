"""Contradiction management."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ContradictionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ContradictionRecord(BaseModel):
    contradiction_id: str = Field(default_factory=lambda: f"contr-{uuid.uuid4().hex[:8]}")
    claim: str
    source_a: str
    source_b: str
    evidence_a: str = ""
    evidence_b: str = ""
    severity: ContradictionSeverity = ContradictionSeverity.MEDIUM
    confidence_a: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_b: float = Field(default=0.5, ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_notes: str = ""
    metadata: dict = Field(default_factory=dict)


def detect_contradiction(claim: str, source_a: str, value_a: str, confidence_a: float, source_b: str, value_b: str, confidence_b: float) -> Optional[ContradictionRecord]:
    if value_a.strip().lower() != value_b.strip().lower():
        severity = ContradictionSeverity.HIGH if abs(confidence_a - confidence_b) < 0.2 else ContradictionSeverity.MEDIUM
        return ContradictionRecord(
            claim=claim,
            source_a=source_a,
            source_b=source_b,
            evidence_a=value_a,
            evidence_b=value_b,
            severity=severity,
            confidence_a=confidence_a,
            confidence_b=confidence_b
        )
    return None


def resolve_contradiction(record: ContradictionRecord, resolution_notes: str) -> ContradictionRecord:
    record.resolved = True
    record.resolution_notes = resolution_notes
    return record


def list_unresolved(records: List[ContradictionRecord]) -> List[ContradictionRecord]:
    return [r for r in records if not r.resolved]
