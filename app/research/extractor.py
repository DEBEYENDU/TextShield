"""Knowledge extraction."""

from __future__ import annotations
import uuid
from .models import KnowledgeItem
from .enums import KnowledgeState

class KnowledgeExtractor:
    def extract_from_evidence(self, evidence) -> KnowledgeItem:
        # Simplified extraction
        item = KnowledgeItem(
            knowledge_id=f"kn-{uuid.uuid4().hex[:8]}",
            research_id=evidence.research_id,
            entity_type="domain",
            entity_value=evidence.observed_value,
            attributes={"claim": evidence.claim, "source_id": evidence.source_id},
            confidence=evidence.confidence,
            state=KnowledgeState.EXTRACTED
        )
        return item
