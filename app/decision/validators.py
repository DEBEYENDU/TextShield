from __future__ import annotations

from typing import Dict, List, Optional, Any

from dataclasses import dataclass, field

from app.decision.weighting import WeightingConfig, DecisionThresholds
from app.decision.evidence_fusion import SignalInputs, FusionResult


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    normalized_inputs: Optional[SignalInputs] = None


class InputValidators:
    """Validators for decision engine inputs."""

    @staticmethod
    def validate_signal_input(name: str, data: Any, expected_type: type = dict) -> bool:
        """Validate a single signal input."""
        if data is None:
            return True  # None is acceptable - will be treated as empty
        if not isinstance(data, expected_type):
            return False
        return True

    @staticmethod
    def validate_confidence(value: Any) -> bool:
        """Validate a confidence score is in valid range."""
        try:
            c = float(value)
            return 0.0 <= c <= 1.0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_classification(
        value: Any, valid_classes: Optional[List[str]] = None
    ) -> bool:
        """Validate a classification value."""
        if value is None:
            return True
        if valid_classes and value not in valid_classes:
            return False
        return True

    @staticmethod
    def validate_signal_inputs(inputs: SignalInputs) -> ValidationResult:
        """Validate all signal inputs and return normalized result."""
        errors = []
        warnings = []

        # Check each signal component
        if inputs.semantic and not isinstance(inputs.semantic, dict):
            errors.append("semantic signal must be a dict or None")

        if inputs.intent and not isinstance(inputs.intent, dict):
            errors.append("intent signal must be a dict or None")

        if inputs.behavior and not isinstance(inputs.behavior, dict):
            errors.append("behavior signal must be a dict or None")

        if inputs.retrieval and not isinstance(inputs.retrieval, dict):
            errors.append("retrieval signal must be a dict or None")

        if inputs.llm and not isinstance(inputs.llm, dict):
            errors.append("llm signal must be a dict or None")

        if inputs.ml and not isinstance(inputs.ml, dict):
            errors.append("ml signal must be a dict or None")

        if inputs.historical and not isinstance(inputs.historical, dict):
            errors.append("historical signal must be a dict or None")

        if inputs.entities and not isinstance(inputs.entities, dict):
            errors.append("entities signal must be a dict or None")

        # Validate confidence values
        if inputs.semantic and "confidence" in inputs.semantic:
            if not InputValidators.validate_confidence(inputs.semantic["confidence"]):
                errors.append("semantic confidence must be 0-1")

        if inputs.llm and "confidence" in inputs.llm:
            if not InputValidators.validate_confidence(inputs.llm["confidence"]):
                errors.append("LLM confidence must be 0-1")

        if inputs.ml and "confidence" in inputs.ml:
            if not InputValidators.validate_confidence(inputs.ml["confidence"]):
                errors.append("ML confidence must be 0-1")

        # Check for completely empty inputs
        all_empty = all(
            not getattr(inputs, name, None)
            for name in [
                "semantic",
                "intent",
                "behavior",
                "retrieval",
                "llm",
                "ml",
                "entities",
            ]
        )
        if all_empty:
            warnings.append("No signal inputs provided - decision may be unreliable")

        valid = len(errors) == 0
        normalized = inputs if valid else None

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            normalized_inputs=normalized,
        )

    @staticmethod
    def validate_fusion_result(fusion_result: FusionResult) -> ValidationResult:
        """Validate a fusion result."""
        errors = []
        warnings = []

        if fusion_result is None:
            return ValidationResult(
                valid=False, errors=["Fusion result is None"], warnings=[]
            )

        # Check classification is valid
        if fusion_result.classification not in ["Spam", "Suspicious", "Ham", "Unknown"]:
            errors.append(f"Invalid classification: {fusion_result.classification}")

        # Check risk level is valid
        if fusion_result.risk_level not in [
            "Very Low",
            "Low",
            "Medium",
            "High",
            "Critical",
        ]:
            errors.append(f"Invalid risk level: {fusion_result.risk_level}")

        # Check confidence is in range
        if not InputValidators.validate_confidence(fusion_result.confidence):
            errors.append("Confidence must be 0-1")

        # Check weighted score is in range
        if not InputValidators.validate_confidence(fusion_result.weighted_score):
            errors.append("Weighted score must be 0-1")

        valid = len(errors) == 0
        (
            warnings.append("Fusion result validation completed")
            if valid
            else warnings.append("Fusion result validation failed")
        )

        return ValidationResult(valid=valid, errors=errors, warnings=warnings)


@dataclass
class PipelineValidator:
    """Validates the full analysis pipeline output."""

    @staticmethod
    def validate_decision_output(output: Dict[str, Any]) -> ValidationResult:
        """Validate a decision engine output dictionary."""
        errors = []
        warnings = []

        # Required fields
        required_fields = [
            "classification",
            "risk_level",
            "confidence",
            "signals",
            "evidence",
            "reasoning_summary",
        ]
        for field_name in required_fields:
            if field_name not in output:
                errors.append(f"Missing required field: {field_name}")

        # Validate classification
        if "classification" in output:
            valid_classes = ["Spam", "Suspicious", "Ham", "Unknown"]
            if output["classification"] not in valid_classes:
                errors.append(f"Invalid classification: {output['classification']}")

        # Validate risk level
        if "risk_level" in output:
            valid_risks = ["Very Low", "Low", "Medium", "High", "Critical"]
            if output["risk_level"] not in valid_risks:
                errors.append(f"Invalid risk level: {output['risk_level']}")

        # Validate confidence
        if "confidence" in output:
            if not InputValidators.validate_confidence(output["confidence"]):
                errors.append("Confidence must be 0-1")

        # Validate signals
        if "signals" in output:
            signals = output["signals"]
            # Check expected signal structure
            expected_signal_keys = [
                "semantic",
                "intent",
                "behavior",
                "retrieval",
                "llm",
                "ml",
            ]
            for key in expected_signal_keys:
                if key in signals:
                    # Basic validation
                    if not isinstance(signals[key], dict):
                        errors.append(f"Signal '{key}' must be a dict")

        # Validate reasoning summary
        if "reasoning_summary" in output:
            if (
                not isinstance(output["reasoning_summary"], str)
                or len(output["reasoning_summary"]) < 10
            ):
                errors.append(
                    "Reasoning summary must be a string of at least 10 characters"
                )

        # Validate recommendations if present
        if "recommendations" in output:
            recs = output["recommendations"]
            if not isinstance(recs, list):
                errors.append("Recommendations must be a list")
            else:
                for i, rec in enumerate(recs):
                    if not isinstance(rec, dict):
                        errors.append(f"Recommendation {i} must be a dict")
                    else:
                        # Check recommendation has required fields
                        if "recommendation" not in rec:
                            errors.append(
                                f"Recommendation {i} missing 'recommendation' field"
                            )

        # Validate references if present
        if "references" in output:
            refs = output["references"]
            if not isinstance(refs, list):
                errors.append("References must be a list")

        valid = len(errors) == 0
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
