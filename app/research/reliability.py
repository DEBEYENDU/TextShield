"""Source reliability and contradiction handling."""

from __future__ import annotations
from .models import Evidence, Contradiction
from .enums import ContradictionState
import uuid

class ReliabilityEngine:
    def score(self, evidence: Evidence) -> float:
        # Simplified scoring
        return evidence.reliability * evidence.freshness * evidence.confidence

class ContradictionEngine:
    def detect(self, evidences: list[Evidence]) -> list[Contradiction]:
        contradictions = []
        # Simplified pairwise detection
        for i in range(len(evidences)):
            for j in range(i+1, len(evidences)):
                a = evidences[i]
                b = evidences[j]
                if a.claim == b.claim and a.observed_value != b.observed_value:
                    contradictions.append(Contradiction(
                        contradiction_id=f"con-{uuid.uuid4().hex[:8]}",
                        research_id=a.research_id,
                        evidence_id_a=a.evidence_id,
                        evidence_id_b=b.evidence_id,
                        claim=a.claim,
                        state=ContradictionState.UNRESOLVED
                    ))
        return contradictions
