"""Evidence fusion."""

from __future__ import annotations
from .models import Evidence, KnowledgeItem
from .enums import KnowledgeState

class EvidenceFusionEngine:
    def fuse(self, evidences: list[Evidence]) -> KnowledgeItem:
        # Simplified fusion: average confidence
        if not evidences:
            raise ValueError("No evidences to fuse")
        avg_conf = sum(e.reliability * e.freshness * e.confidence for e in evidences) / len(evidences)
        import uuid
        item = KnowledgeItem(
            knowledge_id=f"kn-{uuid.uuid4().hex[:8]}",
            research_id=evidences[0].research_id,
            entity_type="fused",
            entity_value=evidences[0].observed_value,
            confidence=max(0.0, min(1.0, avg_conf)),
            state=KnowledgeState.VALIDATED
        )
        return item
