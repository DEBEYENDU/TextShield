from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class ThreatSeverity(Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatProfile:
    """Unified threat profile resulting from evidence aggregation.

    Attributes:
        overall_threat_score: Composite score 0.0 - 1.0
        confidence: Aggregated confidence 0.0 - 1.0
        severity: Mapped severity level
        provider_agreement: Ratio of providers agreeing (0.0 - 1.0)
        supporting_evidence: List of evidence supporting the conclusion
        conflicting_evidence: List of evidence contradicting the conclusion
        evidence_count: Total number of evidence items considered
        reliability_score: Provider reliability aggregation 0.0 - 1.0
        reasoning_summary: Human-readable explanation string
        timestamp: When the profile was computed
    """

    def __init__(
        self,
        overall_threat_score: float = 0.0,
        confidence: float = 0.0,
        severity: ThreatSeverity = ThreatSeverity.LOW,
        provider_agreement: float = 0.0,
        supporting_evidence: Optional[List[dict]] = None,
        conflicting_evidence: Optional[List[dict]] = None,
        evidence_count: int = 0,
        reliability_score: float = 0.0,
        reasoning_summary: str = "",
        timestamp: Optional[datetime] = None,
    ):
        self.overall_threat_score = overall_threat_score
        self.confidence = confidence
        self.severity = severity
        self.provider_agreement = provider_agreement
        self.supporting_evidence = supporting_evidence or []
        self.conflicting_evidence = conflicting_evidence or []
        self.evidence_count = evidence_count
        self.reliability_score = reliability_score
        self.reasoning_summary = reasoning_summary
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        sev_val = self.severity.value if isinstance(self.severity, Enum) else self.severity
        return {
            "overall_threat_score": self.overall_threat_score,
            "confidence": self.confidence,
            "severity": sev_val,
            "provider_agreement": self.provider_agreement,
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "evidence_count": self.evidence_count,
            "reliability_score": self.reliability_score,
            "reasoning_summary": self.reasoning_summary,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatProfile":
        sev_str = data.get("severity", "low")
        severity = ThreatSeverity(sev_str) if isinstance(sev_str, str) else sev_str
        return cls(
            overall_threat_score=data.get("overall_threat_score", 0.0),
            confidence=data.get("confidence", 0.0),
            severity=severity,
            provider_agreement=data.get("provider_agreement", 0.0),
            supporting_evidence=data.get("supporting_evidence", []),
            conflicting_evidence=data.get("conflicting_evidence", []),
            evidence_count=data.get("evidence_count", 0),
            reliability_score=data.get("reliability_score", 0.0),
            reasoning_summary=data.get("reasoning_summary", ""),
            timestamp=data.get("timestamp"),
        )