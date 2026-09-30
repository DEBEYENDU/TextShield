"""Evidence provenance tracking."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    provenance_id: str = Field(default_factory=lambda: f"prov-{uuid.uuid4().hex[:8]}")
    entity_id: Optional[str] = None
    candidate_id: Optional[str] = None
    source_id: str
    source_type: str
    evidence_hash: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    origin_tool: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    lineage: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


def create_provenance(entity_id: Optional[str], source_id: str, source_type: str, evidence_hash: str, origin_tool: str = "", confidence: float = 0.5) -> ProvenanceRecord:
    return ProvenanceRecord(
        entity_id=entity_id,
        source_id=source_id,
        source_type=source_type,
        evidence_hash=evidence_hash,
        origin_tool=origin_tool,
        confidence=confidence
    )


def add_lineage(record: ProvenanceRecord, parent_id: str) -> ProvenanceRecord:
    if parent_id not in record.lineage:
        record.lineage.append(parent_id)
    return record


def verify_chain(records: List[ProvenanceRecord]) -> bool:
    # Simple verification: all records have source_id and hash non-empty
    for r in records:
        if not r.source_id or not r.evidence_hash:
            return False
    return True
