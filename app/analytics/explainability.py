from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime


class ExplanationRecord:
    """Represents an explainability record for an analysis."""

    def __init__(
        self,
        analysis_id: str,
        classification: str,
        confidence: float,
        risk_level: str,
        supporting_evidence: List[Dict[str, Any]],
        retrieved_knowledge: List[Dict[str, Any]],
        intent_analysis: Optional[Dict[str, Any]] = None,
        behavior_analysis: Optional[Dict[str, Any]] = None,
        ml_contribution: Optional[Dict[str, Any]] = None,
        llm_contribution: Optional[Dict[str, Any]] = None,
        decision_weights: Optional[Dict[str, float]] = None,
        reasoning_summary: Optional[str] = None,
        limitations: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.analysis_id = analysis_id
        self.classification = classification
        self.confidence = confidence
        self.risk_level = risk_level
        self.supporting_evidence = supporting_evidence or []
        self.retrieved_knowledge = retrieved_knowledge or []
        self.intent_analysis = intent_analysis or {}
        self.behavior_analysis = behavior_analysis or {}
        self.ml_contribution = ml_contribution or {}
        self.llm_contribution = llm_contribution or {}
        self.decision_weights = decision_weights or {}
        self.reasoning_summary = reasoning_summary or ""
        self.limitations = limitations or []
        self.recommendations = recommendations or []
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "classification": self.classification,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "supporting_evidence": self.supporting_evidence,
            "retrieved_knowledge": self.retrieved_knowledge,
            "intent_analysis": self.intent_analysis,
            "behavior_analysis": self.behavior_analysis,
            "ml_contribution": self.ml_contribution,
            "llm_contribution": self.llm_contribution,
            "decision_weights": self.decision_weights,
            "reasoning_summary": self.reasoning_summary,
            "limitations": self.limitations,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExplanationRecord":
        from datetime import datetime

        return cls(
            analysis_id=data.get("analysis_id", ""),
            classification=data.get("classification", ""),
            confidence=data.get("confidence", 0.0),
            risk_level=data.get("risk_level", "Unknown"),
            supporting_evidence=data.get("supporting_evidence", []),
            retrieved_knowledge=data.get("retrieved_knowledge", []),
            intent_analysis=data.get("intent_analysis"),
            behavior_analysis=data.get("behavior_analysis"),
            ml_contribution=data.get("ml_contribution"),
            llm_contribution=data.get("llm_contribution"),
            decision_weights=data.get("decision_weights"),
            reasoning_summary=data.get("reasoning_summary"),
            limitations=data.get("limitations"),
            recommendations=data.get("recommendations"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else None
            ),
        )


class ExplainabilityEngine:
    """Engine for generating explainability reports."""

    @staticmethod
    def generate_explanation(analysis_record: Dict[str, Any]) -> ExplanationRecord:
        """Generate an explanation record from an analysis."""
        return ExplanationRecord(
            analysis_id=analysis_record.get("id", ""),
            classification=analysis_record.get("classification", "Unknown"),
            confidence=analysis_record.get("confidence", 0.0),
            risk_level=analysis_record.get("risk_level", "Unknown"),
            supporting_evidence=analysis_record.get("evidence", []),
            retrieved_knowledge=analysis_record.get("rag_evidence", []),
            intent_analysis=analysis_record.get("intent", {}),
            behavior_analysis=analysis_record.get("behavior", {}),
            ml_contribution=analysis_record.get("ml_contribution", {}),
            llm_contribution=analysis_record.get("llm_contribution", {}),
            decision_weights=analysis_record.get("decision_weights", {}),
            reasoning_summary=analysis_record.get("reasoning_summary", ""),
            limitations=analysis_record.get("limitations", []),
            recommendations=analysis_record.get("recommendations", []),
        )


class ExplainabilityReportGenerator:
    @staticmethod
    def generate_classification_report(
        explanations: List[ExplanationRecord],
    ) -> Dict[str, Any]:
        if not explanations:
            return {"error": "No explanations found"}

        return {
            "total_explanations": len(explanations),
            "classification_distribution": {
                exp.classification: sum(
                    1 for e in explanations if e.classification == exp.classification
                )
                for exp in explanations
            },
            "average_confidence": (
                sum(e.confidence for e in explanations) / len(explanations)
                if explanations
                else 0
            ),
            "risk_distribution": (
                {
                    exp.risk_level: sum(
                        1 for e in explanations if e.risk_level == exp.risk_level
                    )
                    for exp in explanations
                }
                if explanations
                else {}
            ),
        }

    @staticmethod
    def generate_evidence_report(
        explanations: List[ExplanationRecord],
    ) -> Dict[str, Any]:
        if not explanations:
            return {"error": "No explanations found"}

        all_evidence = []
        for exp in explanations:
            all_evidence.extend(exp.supporting_evidence)

        return {
            "total_explanations": len(explanations),
            "total_evidence_items": len(all_evidence),
            "evidence_sources": list(
                set(e.get("source", "unknown") for e in all_evidence)
            ),
            "evidence_by_type": {
                type_: sum(1 for e in all_evidence if e.get("type") == type_)
                for type_ in set(e.get("type", "unknown") for e in all_evidence)
            },
        }
