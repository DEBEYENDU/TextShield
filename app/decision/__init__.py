from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass, field

from app.ml_engine.__init__ import (
    BaseMLModel,
    MODEL_REGISTRY,
    get_model,
    LogisticRegressionModel,
    LinearSVMModel,
    RandomForestModel,
    NaiveBayesModel,
    MLFeatureExtractor,
    train_ml_pipeline,
    predict_ml,
    evaluate_ml,
)

from app.reasoning.__init__ import (
    EvidenceValidator,
    PromptBuilder,
    PromptInjectionProtector,
    quick_estimate_confidence,
    parse_llm_response,
    parse_and_validate_llm_output,
    estimate_confidence,
    sanitize_user_input,
)

from app.decision.decision_engine import (
    DecisionEngine,
    DecisionOutput,
    Explanation,
    RiskEngine,
    ConfidenceEngine,
    RecommendationEngine,
    EvidenceFusion,
    WeightingConfig,
    DecisionSignals,
    RiskFactors,
)

from app.decision.weighting import WeightingConfig as WC, DecisionThresholds as DT
from app.decision.config import DecisionEngineConfig, PipelineConfig
from app.decision.validators import InputValidators, PipelineValidator, ValidationResult
from app.decision.utils import (
    merge_dicts,
    format_confidence_label,
    format_risk_label,
    generate_reasoning_summary,
    sanitize_input,
    TimestampedValue,
    ProcessingMetrics,
    DecisionLogEntry,
)

__all__ = [
    "DecisionEngine",
    "RiskEngine",
    "ConfidenceEngine",
    "RecommendationEngine",
    "EvidenceFusion",
    "WeightingConfig",
    "DecisionSignals",
    "RiskFactors",
    "Explanation",
    "DecisionOutput",
    "DecisionEngineConfig",
    "PipelineConfig",
]
