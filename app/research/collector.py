"""Evidence collector and normalizer."""

from __future__ import annotations
from .models import Evidence
from .enums import EvidenceType, SourceType

class EvidenceCollector:
    def collect(self, source_id: str, research_id: str, claim: str, observed_value: str, source_type: SourceType, evidence_type: EvidenceType = EvidenceType.OBSERVED) -> Evidence:
        import uuid
        ev = Evidence(
            evidence_id=f"ev-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            source_id=source_id,
            source_type=source_type,
            claim=claim,
            observed_value=observed_value,
            evidence_type=evidence_type
        )
        return ev

class EvidenceNormalizer:
    def normalize(self, evidence: Evidence) -> Evidence:
        # Simplified normalization
        evidence.claim = evidence.claim.strip().lower()
        evidence.observed_value = evidence.observed_value.strip()
        return evidence
