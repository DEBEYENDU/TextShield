from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum


class EvidenceSource(Enum):
    THREAT_INTELLIGENCE = "threat_intelligence"
    HYBRID_ML = "hybrid_ml"
    LLM_REASONING = "llm_reasoning"
    RAG_RETRIEVAL = "rag_retrieval"
    RULE_ENGINE = "rule_engine"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    INTENT_ANALYSIS = "intent_analysis"
    CUSTOM = "custom"


class EvidenceItem:
    """Unified evidence item shared across all subsystems.

    Attributes:
        source: Which subsystem produced the evidence.
        timestamp: When the evidence was created.
        confidence: Confidence score 0.0 - 1.0.
        weight: Source-specific weight.
        summary: Human-readable summary of the evidence.
        raw_evidence: Original unprocessed data (dict or string).
        structured_evidence: Parsed, normalized representation.
        supporting_artifacts: List of artifact IDs or references that support this evidence.
        metadata: Additional key-value metadata.
        evidence_id: Unique identifier for traceability.
    """

    def __init__(
        self,
        source: EvidenceSource,
        timestamp: Optional[datetime] = None,
        confidence: float = 0.5,
        weight: float = 1.0,
        summary: str = "",
        raw_evidence: Any = None,
        structured_evidence: Optional[Dict[str, Any]] = None,
        supporting_artifacts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        evidence_id: Optional[str] = None,
    ):
        self.evidence_id = evidence_id or str(uuid4())
        self.source = source
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.confidence = confidence
        self.weight = weight
        self.summary = summary
        self.raw_evidence = raw_evidence
        self.structured_evidence = structured_evidence or {}
        self.supporting_artifacts = supporting_artifacts or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "weight": self.weight,
            "summary": self.summary,
            "raw_evidence": self.raw_evidence,
            "structured_evidence": self.structured_evidence,
            "supporting_artifacts": self.supporting_artifacts,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        from uuid import uuid4
        item = cls(
            source=EvidenceSource(data["source"]),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            confidence=data.get("confidence", 0.5),
            weight=data.get("weight", 1.0),
            summary=data.get("summary", ""),
            raw_evidence=data.get("raw_evidence"),
            structured_evidence=data.get("structured_evidence", {}),
            supporting_artifacts=data.get("supporting_artifacts", []),
            metadata=data.get("metadata", {}),
            evidence_id=data.get("evidence_id"),
        )
        return item


# Simple UUID helper (in real code import from uuid)
def uuid4() -> str:
    import uuid
    return str(uuid.uuid4())