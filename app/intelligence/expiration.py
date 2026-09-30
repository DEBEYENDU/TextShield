"""Knowledge expiration workflow."""

from __future__ import annotations
from datetime import datetime
from .governance import KnowledgeGovernanceRecord, expire as gov_expire


def expire_records(records: list[KnowledgeGovernanceRecord], max_age_days: int = 365) -> int:
    expired = 0
    for r in records:
        old_state = r.state
        gov_expire(r, max_age_days)
        if r.state.value == "EXPIRED" and old_state != r.state:
            expired += 1
    return expired


def is_expired(record: KnowledgeGovernanceRecord, max_age_days: int = 365) -> bool:
    age = (datetime.utcnow() - record.created_at).days
    return age > max_age_days and record.state in {"APPROVED", "DEPRECATED"}
