from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from dataclasses import dataclass, field

import json
import time


@dataclass
class TimestampedValue:
    """A value with an associated timestamp."""

    value: Any
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    ttl: Optional[float] = None  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if the value has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "expired": self.is_expired(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimestampedValue":
        return cls(
            value=data.get("value"),
            timestamp=data.get("timestamp", time.time()),
            source=data.get("source", "unknown"),
            ttl=data.get("ttl"),
        )


@dataclass
class ProcessingMetrics:
    """Metrics for decision engine processing."""

    total_processing_time: float = 0.0
    signal_processing_time: float = 0.0
    fusion_time: float = 0.0
    risk_time: float = 0.0
    confidence_time: float = 0.0
    recommendation_time: float = 0.0
    explanation_time: float = 0.0

    # Breakdown
    per_signal_times: Dict[str, float] = field(default_factory=dict)
    evidence_count: int = 0
    input_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_processing_time": self.total_processing_time,
            "signal_processing_time": self.signal_processing_time,
            "fusion_time": self.fusion_time,
            "risk_time": self.risk_time,
            "confidence_time": self.confidence_time,
            "recommendation_time": self.recommendation_time,
            "explanation_time": self.explanation_time,
            "evidence_count": self.evidence_count,
            "input_count": self.input_count,
            "per_signal_times": self.per_signal_times,
        }


def merge_dicts(
    dicts: List[Dict[str, Any]], conflict_strategy: str = "weighted_average"
) -> Dict[str, Any]:
    """Merge multiple dictionaries with a conflict resolution strategy."""
    if not dicts:
        return {}
    if len(dicts) == 1:
        return dicts[0].copy()

    result = {}

    # Collect all keys
    all_keys = set()
    for d in dicts:
        all_keys.update(d.keys())

    for key in all_keys:
        values = [d[key] for d in dicts if key in d]

        if not values:
            continue

        if len(values) == 1:
            result[key] = values[0]
        else:
            # Apply conflict resolution strategy
            if conflict_strategy == "weighted_average":
                # Try to use weights if available
                weighted_sum = 0.0
                total_weight = 0.0
                for v in values:
                    if isinstance(v, (int, float)):
                        # Default equal weighting
                        weighted_sum += v
                        total_weight += 1.0
                    elif isinstance(v, dict):
                        # Use a simple approach - merge dicts recursively
                        pass

                if weighted_sum > 0 and total_weight > 0:
                    result[key] = weighted_sum / total_weight
                else:
                    result[key] = values[0]

            elif conflict_strategy == "priority":
                # Use the first value (priority order)
                result[key] = values[0]

            elif conflict_strategy == " majority":
                # For numerical values, use majority
                if all(isinstance(v, (int, float)) for v in values):
                    from collections import Counter

                    counter = Counter(values)
                    result[key] = counter.most_common(1)[0][0]
                else:
                    result[key] = values[0]

            else:
                result[key] = values[0]

    return result


def format_confidence_label(confidence: float) -> str:
    """Format a confidence value as a human-readable label."""
    if confidence >= 0.8:
        return "Very High"
    elif confidence >= 0.6:
        return "High"
    elif confidence >= 0.4:
        return "Moderate"
    elif confidence >= 0.2:
        return "Low"
    else:
        return "Very Low"


def format_risk_label(risk_level: str) -> str:
    """Format a risk level as a human-readable label."""
    labels = {
        "Very Low": "Minimal risk",
        "Low": "Low risk",
        "Medium": "Medium risk - exercise caution",
        "High": "High risk - take precautions",
        "Critical": "Critical risk - immediate action recommended",
    }
    return labels.get(risk_level, risk_level)


def generate_reasoning_summary(
    classification: str,
    risk_level: str,
    contributing_factors: List[str],
    conflicting: bool = False,
) -> str:
    """Generate a standardized reasoning summary."""
    parts = []

    # Classification part
    if classification == "Spam":
        parts.append("Message classified as spam")
    elif classification == "Suspicious":
        parts.append("Message classified as suspicious")
    elif classification == "Ham":
        parts.append("Message classified as legitimate")

    # Risk part
    risk_labels = {
        "Very Low": "very low risk",
        "Low": "low risk",
        "Medium": "medium risk",
        "High": "high risk",
        "Critical": "critical risk",
    }
    parts.append(f"with {risk_labels.get(risk_level, risk_level)}")

    # Contributing factors
    if contributing_factors:
        factors_str = " based on: " + ", ".join(contributing_factors[:3])
        if len(contributing_factors) > 3:
            factors_str += f" and {len(contributing_factors) - 3} other factors"
        parts.append(factors_str)

    # Conflicting evidence
    if conflicting:
        parts.append("with conflicting evidence from subsystems")

    return " ".join(parts)


def sanitize_input(text: str) -> str:
    """Sanitize text input to prevent injection attacks."""
    if not isinstance(text, str):
        return str(text)
    # Remove potential injection sequences
    dangerous_patterns = [
        "<script",
        "</script>",
        "javascript:",
        "onerror=",
        "onload=",
    ]
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, "")
    return sanitized.strip()


@dataclass
class DecisionLogEntry:
    """Log entry for decision engine processing."""

    timestamp: float = field(default_factory=time.time)
    input_hash: str = ""
    classification: str = ""
    risk_level: str = ""
    confidence: float = 0.0
    signals_summary: str = ""
    recommendations_count: int = 0
    processing_time: float = 0.0
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "classification": self.classification,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "signals_summary": self.signals_summary,
            "recommendations_count": self.recommendations_count,
            "processing_time": self.processing_time,
            "version": self.version,
        }
