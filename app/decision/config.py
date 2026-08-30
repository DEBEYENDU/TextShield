from __future__ import annotations

from typing import Dict, Any, Optional

from dataclasses import dataclass, field

from app.decision.weighting import WeightingConfig, DecisionThresholds


@dataclass
class DecisionEngineConfig:
    """Configuration for the Decision Engine."""

    # Weighting configuration
    weighting_config: WeightingConfig = field(default_factory=WeightingConfig)

    # Decision thresholds
    decision_thresholds: DecisionThresholds = field(default_factory=DecisionThresholds)

    # Signal priorities (for fallback ordering)
    signal_priorities: List[str] = field(
        default_factory=lambda: [
            "llm",
            "retrieval",
            "ml",
            "semantic",
            "intent",
            "behavior",
            "historical",
            "entities",
        ]
    )

    # Default weights per signal category
    default_signal_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "semantic": 1.0,
            "intent": 1.0,
            "behavior": 1.0,
            "retrieval": 1.0,
            "llm": 1.0,
            "ml": 1.0,
            "historical": 0.5,
            "entities": 0.5,
        }
    )

    # Classification labels
    classification_labels: List[str] = field(
        default_factory=lambda: ["Spam", "Suspicious", "Ham", "Unknown"]
    )

    # Risk level labels
    risk_levels: List[str] = field(
        default_factory=lambda: [
            "Very Low",
            "Low",
            "Medium",
            "High",
            "Critical",
        ]
    )

    # Recommendation rules configuration
    recommendation_rules: Dict[str, Any] = field(default_factory=dict)

    # Conflict resolution strategy
    conflict_strategy: str = "weighted_fusion"

    # Whether to include ML in decisions
    include_ml: bool = True

    # Whether to include LLM in decisions
    include_llm: bool = True

    # Whether to include RAG in decisions
    include_rag: bool = True

    def get_weight(self, signal: str) -> float:
        """Get the weight for a specific signal."""
        if hasattr(self.weighting_config, signal):
            return getattr(self.weighting_config, signal)
        return self.default_signal_weights.get(signal, 1.0)

    def adjust_weights(self, **kwargs: float) -> DecisionEngineConfig:
        """Adjust specific weights."""
        config = DecisionEngineConfig()
        config.weighting_config = self.weighting_config.normalize()
        for key, value in kwargs.items():
            if hasattr(config.weighting_config, key):
                setattr(config.weighting_config, key, value)
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "weighting_config": {
                "semantic_weight": self.weighting_config.semantic_weight,
                "intent_weight": self.weighting_config.intent_weight,
                "behavior_weight": self.weighting_config.behavior_weight,
                "retrieval_confidence_weight": self.weighting_config.retrieval_confidence_weight,
                "knowledge_trust_weight": self.weighting_config.knowledge_trust_weight,
                "llm_confidence_weight": self.weighting_config.llm_confidence_weight,
                "llm_reasoning_weight": self.weighting_config.llm_reasoning_weight,
                "ml_probability_weight": self.weighting_config.ml_probability_weight,
                "ml_contribution_weight": self.weighting_config.ml_contribution_weight,
                "historical_consistency_weight": self.weighting_config.historical_consistency_weight,
                "entity_confidence_weight": self.weighting_config.entity_confidence_weight,
                "overall_weight": self.weighting_config.overall_weight,
            },
            "decision_thresholds": {
                "high_confidence_threshold": self.decision_thresholds.high_confidence_threshold,
                "medium_confidence_threshold": self.decision_thresholds.medium_confidence_threshold,
                "low_confidence_threshold": self.decision_thresholds.low_confidence_threshold,
                "critical_risk_threshold": self.decision_thresholds.critical_risk_threshold,
                "high_risk_threshold": self.decision_thresholds.high_risk_threshold,
                "medium_risk_threshold": self.decision_thresholds.medium_risk_threshold,
                "low_risk_threshold": self.decision_thresholds.low_risk_threshold,
                "urgent_recommendation_threshold": self.decision_thresholds.urgent_recommendation_threshold,
                "caution_recommendation_threshold": self.decision_thresholds.caution_recommendation_threshold,
            },
            "signal_priorities": self.signal_priorities,
            "classification_labels": self.classification_labels,
            "risk_levels": self.risk_levels,
            "include_ml": self.include_ml,
            "include_llm": self.include_llm,
            "include_rag": self.include_rag,
        }


@dataclass
class PipelineConfig:
    """Configuration for the analysis pipeline integration."""

    # Integration settings
    enable_decision_engine: bool = True
    enable_risk_engine: bool = True
    enable_confidence_engine: bool = True
    enable_recommendations: bool = True

    # Output settings
    include_explanation: bool = True
    include_evidence: bool = True
    include_recommendations: bool = True

    # API settings
    return_json: bool = True
    verbose_output: bool = False

    # Performance settings
    optimize_latency: bool = True
    max_evidence_items: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_decision_engine": self.enable_decision_engine,
            "enable_risk_engine": self.enable_risk_engine,
            "enable_confidence_engine": self.enable_confidence_engine,
            "enable_recommendations": self.enable_recommendations,
            "include_explanation": self.include_explanation,
            "include_evidence": self.include_evidence,
            "include_recommendations": self.include_recommendations,
            "return_json": self.return_json,
            "verbose_output": self.verbose_output,
            "optimize_latency": self.optimize_latency,
            "max_evidence_items": self.max_evidence_items,
        }
