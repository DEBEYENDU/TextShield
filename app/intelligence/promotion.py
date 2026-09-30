"""Knowledge promotion workflow."""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from .governance import KnowledgeGovernanceRecord, GovernanceState


def should_promote(record: KnowledgeGovernanceRecord) -> bool:
    if record.state != GovernanceState.DRAFT:
        return False
    return record.confidence >= 0.8 and record.evidence_count >= 1


def promote_candidate(record: KnowledgeGovernanceRecord, reviewer_id: Optional[str] = None) -> KnowledgeGovernanceRecord:
    from .governance import promote
    if should_promote(record):
        record.state = GovernanceState.PENDING_REVIEW
    record.updated_at = datetime.utcnow()
    return promote(record, reviewer_id)


def auto_promote(records: list[KnowledgeGovernanceRecord]) -> int:
    count = 0
    for r in records:
        if should_promote(r):
            promote_candidate(r)
            count += 1
    return count
