"""Intelligence candidate repository."""

from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.database.base import get_connection
from .models import ResearchCandidate
from .enums import CandidateState, CandidateType, CandidateSource


def _row_to_candidate(row: sqlite3.Row) -> ResearchCandidate:
    return ResearchCandidate(
        candidate_id=row["candidate_id"],
        candidate_type=CandidateType(row["candidate_type"]),
        title=row["title"],
        description=row["description"],
        source=CandidateSource(row["source"]),
        source_id=row["source_id"],
        priority=row["priority"],
        urgency=row["urgency"],
        confidence=row["confidence"],
        evidence_count=row["evidence_count"],
        first_seen=datetime.fromisoformat(row["first_seen"]),
        last_seen=datetime.fromisoformat(row["last_seen"]),
        status=CandidateState(row["status"]),
        research_scope=row["research_scope"],
        related_analysis_id=row["related_analysis_id"],
        related_finding_id=row["related_finding_id"],
        related_campaign_id=row["related_campaign_id"],
        related_entity_id=row["related_entity_id"],
        related_ioc_id=row["related_ioc_id"],
        related_research_id=row["related_research_id"],
        related_actor_id=row["related_actor_id"],
        reason=row["reason"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
    )


def create(candidate: ResearchCandidate) -> bool:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO intelligence_candidates
            (candidate_id, candidate_type, title, description, source, source_id,
             priority, urgency, confidence, evidence_count, first_seen, last_seen,
             status, research_scope, related_analysis_id, related_finding_id,
             related_campaign_id, related_entity_id, related_ioc_id,
             related_research_id, related_actor_id, reason, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate.candidate_id,
                candidate.candidate_type.value,
                candidate.title,
                candidate.description,
                candidate.source.value,
                candidate.source_id,
                candidate.priority,
                candidate.urgency,
                candidate.confidence,
                candidate.evidence_count,
                candidate.first_seen.isoformat(),
                candidate.last_seen.isoformat(),
                candidate.status.value,
                candidate.research_scope,
                candidate.related_analysis_id,
                candidate.related_finding_id,
                candidate.related_campaign_id,
                candidate.related_entity_id,
                candidate.related_ioc_id,
                candidate.related_research_id,
                candidate.related_actor_id,
                candidate.reason,
                candidate.created_at.isoformat(),
                candidate.updated_at.isoformat(),
                json.dumps(candidate.metadata)
            )
        )
    return True


def get(candidate_id: str) -> Optional[ResearchCandidate]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM intelligence_candidates WHERE candidate_id = ?",
            (candidate_id,)
        ).fetchone()
    return _row_to_candidate(row) if row else None


def list_all(status: Optional[CandidateState] = None, limit: int = 100, offset: int = 0) -> List[ResearchCandidate]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM intelligence_candidates WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status.value, limit, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM intelligence_candidates ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
    return [_row_to_candidate(r) for r in rows]


def update(candidate: ResearchCandidate) -> bool:
    with get_connection() as conn:
        candidate.updated_at = datetime.utcnow()
        conn.execute(
            """
            UPDATE intelligence_candidates SET
                title = ?, description = ?, priority = ?, urgency = ?, confidence = ?,
                evidence_count = ?, first_seen = ?, last_seen = ?, status = ?, research_scope = ?,
                related_analysis_id = ?, related_finding_id = ?, related_campaign_id = ?,
                related_entity_id = ?, related_ioc_id = ?, related_research_id = ?, related_actor_id = ?,
                reason = ?, updated_at = ?, metadata = ?
            WHERE candidate_id = ?
            """,
            (
                candidate.title,
                candidate.description,
                candidate.priority,
                candidate.urgency,
                candidate.confidence,
                candidate.evidence_count,
                candidate.first_seen.isoformat(),
                candidate.last_seen.isoformat(),
                candidate.status.value,
                candidate.research_scope,
                candidate.related_analysis_id,
                candidate.related_finding_id,
                candidate.related_campaign_id,
                candidate.related_entity_id,
                candidate.related_ioc_id,
                candidate.related_research_id,
                candidate.related_actor_id,
                candidate.reason,
                candidate.updated_at.isoformat(),
                json.dumps(candidate.metadata),
                candidate.candidate_id
            )
        )
    return True


def exists_by_key(candidate_type: CandidateType, source: CandidateSource, related_entity_id: Optional[str], related_ioc_id: Optional[str]) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT candidate_id FROM intelligence_candidates
            WHERE candidate_type = ? AND source = ?
              AND (related_entity_id = ? OR ? IS NULL)
              AND (related_ioc_id = ? OR ? IS NULL)
              AND status NOT IN ('DISMISSED', 'EXPIRED', 'COMPLETED')
            LIMIT 1
            """,
            (candidate_type.value, source.value, related_entity_id, related_entity_id, related_ioc_id, related_ioc_id)
        ).fetchone()
    return row["candidate_id"] if row else None
