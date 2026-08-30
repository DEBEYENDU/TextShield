from __future__ import annotations

from typing import Dict, Any, Optional

from dataclasses import dataclass, field


@dataclass
class WeightingConfig:
    """Configuration for signal weights in evidence fusion."""

    # Semantic understanding weights
    semantic_weight: float = 1.0
    intent_weight: float = 1.0
    behavior_weight: float = 1.0

    # Retrieval weights
    retrieval_confidence_weight: float = 1.0
    knowledge_trust_weight: float = 1.0

    # LLM weights
    llm_confidence_weight: float = 1.0
    llm_reasoning_weight: float = 1.0

    # ML weights
    ml_probability_weight: float = 1.0
    ml_contribution_weight: float = 1.0

    # System weights
    historical_consistency_weight: float = 1.0
    entity_confidence_weight: float = 1.0

    # Overall
    overall_weight: float = 1.0

    def normalize(self) -> "WeightingConfig":
        """Normalize weights so they sum to a reasonable total."""
        total = (
            self.semantic_weight
            + self.intent_weight
            + self.behavior_weight
            + self.retrieval_confidence_weight
            + self.knowledge_trust_weight
            + self.llm_confidence_weight
            + self.llm_reasoning_weight
            + self.ml_probability_weight
            + self.ml_contribution_weight
            + self.historical_consistency_weight
            + self.entity_confidence_weight
            + self.overall_weight
        )
        if total == 0:
            return self
        scale = 1.0 / total
        return WeightingConfig(
            semantic_weight=self.semantic_weight * scale,
            intent_weight=self.intent_weight * scale,
            behavior_weight=self.behavior_weight * scale,
            retrieval_confidence_weight=self.retrieval_confidence_weight * scale,
            knowledge_trust_weight=self.knowledge_trust_weight * scale,
            llm_confidence_weight=self.llm_confidence_weight * scale,
            llm_reasoning_weight=self.llm_reasoning_weight * scale,
            ml_probability_weight=self.ml_probability_weight * scale,
            ml_contribution_weight=self.ml_contribution_weight * scale,
            historical_consistency_weight=self.historical_consistency_weight * scale,
            entity_confidence_weight=self.entity_confidence_weight * scale,
            overall_weight=self.overall_weight * scale,
        )


@dataclass
class DecisionThresholds:
    """Configurable thresholds for decision logic."""

    # Classification thresholds
    high_confidence_threshold: float = 0.7
    medium_confidence_threshold: float = 0.4
    low_confidence_threshold: float = 0.1

    # Risk thresholds
    critical_risk_threshold: float = 0.8
    high_risk_threshold: float = 0.6
    medium_risk_threshold: float = 0.3
    low_risk_threshold: float = 0.1

    # Recommendation thresholds
    urgent_recommendation_threshold: float = 0.7
    caution_recommendation_threshold: float = 0.4

    # ML-specific
    ml_low_probability_threshold: float = 0.2
    ml_high_probability_threshold: float = 0.8

    # LLM-specific
    llm_min_reasoning_score: float = 0.3

    def adjust(self, **kwargs: float) -> DecisionThresholds:
        """Adjust specific thresholds."""
        config = DecisionThresholds()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
