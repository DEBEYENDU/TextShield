"""Evidence provenance tracking."""

from __future__ import annotations
from .models import Evidence

class EvidenceProvenance:
    def track(self, evidence: Evidence) -> dict:
        return {
            "evidence_id": evidence.evidence_id,
            "source_id": evidence.source_id,
            "timestamp": evidence.timestamp.isoformat(),
            "provenance": evidence.provenance
        }
