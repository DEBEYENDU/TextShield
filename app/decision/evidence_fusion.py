from __future__ import annotations

from typing import Dict, List, Optional, Any

from dataclasses import dataclass, field

from app.decision.weighting import WeightingConfig, DecisionThresholds


@dataclass
class SignalInputs:
    """Normalized input signals from all subsystems."""

    semantic: Dict[str, Any] = field(default_factory=dict)
    intent: Dict[str, Any] = field(default_factory=dict)
    behavior: Dict[str, Any] = field(default_factory=dict)
    retrieval: Dict[str, Any] = field(default_factory=dict)
    llm: Dict[str, Any] = field(default_factory=dict)
    ml: Dict[str, Any] = field(default_factory=dict)
    historical: Dict[str, Any] = field(default_factory=dict)
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionResult:
    """Result of evidence fusion."""

    classification: str = "Unknown"
    risk_level: str = "Low"
    confidence: float = 0.0
    weighted_score: float = 0.0
    contributing_signals: Dict[str, float] = field(default_factory=dict)
    conflicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    signal_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)


class EvidenceFusion:
    """Combines evidence from all AI subsystems using configurable weights."""

    def __init__(
        self,
        weighting_config: Optional[WeightingConfig] = None,
        thresholds: Optional[DecisionThresholds] = None,
    ):
        self.weighting_config = weighting_config or WeightingConfig()
        self.thresholds = thresholds or DecisionThresholds()
        self.normalized_weights = self.weighting_config.normalize()

    def normalize_signal(self, signal_name: str, signal_data: Dict[str, Any]) -> float:
        """Normalize a signal to a 0-1 confidence score."""
        if not signal_data:
            return 0.0

        if signal_name == "semantic":
            return signal_data.get("confidence", 0.0)
        elif signal_name == "intent":
            return signal_data.get(
                "confidence", signal_data.get("primary_intent_confidence", 0.0)
            )
        elif signal_name == "behavior":
            return signal_data.get("confidence", 0.0)
        elif signal_name == "retrieval":
            return signal_data.get("confidence", 0.0)
        elif signal_name == "llm":
            return signal_data.get("confidence", 0.0)
        elif signal_name == "ml":
            return signal_data.get("confidence", 0.0)
        elif signal_name == "historical":
            return signal_data.get("consistency", 0.0)
        elif signal_name == "entities":
            return signal_data.get("confidence", 0.0)
        else:
            return signal_data.get("confidence", 0.0)

    def compute_weighted_score(
        self, inputs: SignalInputs, weights: Optional[WeightingConfig] = None
    ) -> float:
        """Compute the weighted fusion score across all signals."""
        w = weights or self.normalized_weights
        score = 0.0
        total_weight = 0.0

        # Semantic
        s = self.normalize_signal("semantic", inputs.semantic)
        score += s * w.semantic_weight
        total_weight += w.semantic_weight

        # Intent
        i = self.normalize_signal("intent", inputs.intent)
        score += i * w.intent_weight
        total_weight += w.intent_weight

        # Behavior
        b = self.normalize_signal("behavior", inputs.behavior)
        score += b * w.behavior_weight
        total_weight += w.behavior_weight

        # Retrieval
        r = self.normalize_signal("retrieval", inputs.retrieval)
        score += r * w.retrieval_confidence_weight
        total_weight += w.retrieval_confidence_weight

        # Knowledge trust
        kt = inputs.retrieval.get("knowledge_trust", 0.5)
        score += kt * w.knowledge_trust_weight
        total_weight += w.knowledge_trust_weight

        # LLM confidence
        l = self.normalize_signal("llm", inputs.llm)
        score += l * w.llm_confidence_weight
        total_weight += w.llm_confidence_weight

        # LLM reasoning quality
        lr = inputs.llm.get("reasoning_quality", 0.5)
        score += lr * w.llm_reasoning_weight
        total_weight += w.llm_reasoning_weight

        # ML probability
        m = self.normalize_signal("ml", inputs.ml)
        score += m * w.ml_probability_weight
        total_weight += w.ml_probability_weight

        # ML contribution
        mc = inputs.ml.get("feature_importance_count", 0.5)
        score += mc * w.ml_contribution_weight
        total_weight += w.ml_contribution_weight

        # Historical consistency
        h = self.normalize_signal("historical", inputs.historical)
        score += h * w.historical_consistency_weight
        total_weight += w.historical_consistency_weight

        # Entity confidence
        e = self.normalize_signal("entities", inputs.entities)
        score += e * w.entity_confidence_weight
        total_weight += w.entity_confidence_weight

        if total_weight == 0:
            return 0.0

        return score / total_weight

    def classify(
        self, weighted_score: float, thresholds: Optional[DecisionThresholds] = None
    ) -> Tuple[str, str, float]:
        """Classify based on weighted score and return (classification, risk_level, confidence)."""
        t = thresholds or self.thresholds

        # Determine classification
        if weighted_score >= t.high_confidence_threshold:
            classification = "Spam"
            risk = "High"
            confidence = min(weighted_score, 1.0)
        elif weighted_score >= t.medium_confidence_threshold:
            classification = "Suspicious"
            risk = "Medium"
            confidence = (weighted_score - t.medium_confidence_threshold) / (
                t.high_confidence_threshold - t.medium_confidence_threshold
            )
            confidence = max(0.0, min(1.0, confidence))
        elif weighted_score >= t.low_confidence_threshold:
            classification = "Ham"
            risk = "Low"
            confidence = (weighted_score - t.low_confidence_threshold) / (
                t.medium_confidence_threshold - t.low_confidence_threshold
            )
            confidence = max(0.0, min(1.0, confidence))
        else:
            classification = "Unknown"
            risk = "Very Low"
            confidence = 0.0

        # Refine risk based on additional factors
        risk = self._refine_risk(
            weighted_score, inputs=None, current_risk=risk, thresholds=t
        )

        return classification, risk, max(0.0, min(1.0, confidence))

    def _refine_risk(
        self,
        weighted_score: float,
        inputs: Optional[SignalInputs],
        current_risk: str,
        thresholds: DecisionThresholds,
    ) -> str:
        """Refine risk level based on detailed signal analysis."""
        if inputs is None:
            return current_risk

        risk_upgrades = []

        # Check for high-risk indicators
        if inputs.llm.get("manipulation_detected", False):
            risk_upgrades.append("upgrade")

        if inputs.ml.get("high_probability_spam", False):
            risk_upgrades.append("upgrade")

        if inputs.retrieval.get("suspicious_links", False):
            risk_upgrades.append("upgrade")

        if inputs.behavior.get("urgency_level") in ["high", "critical"]:
            risk_upgrades.append("upgrade")

        if inputs.intent.get("is_financial", False):
            risk_upgrades.append("upgrade")

        if inputs.entities.get("suspicious_sender", False):
            risk_upgrades.append("upgrade")

        # Check for downgrades
        risk_downgrades = []
        if inputs.semantic.get("confidence", 0) < 0.3:
            risk_downgrades.append("downgrade")
        if inputs.retrieval.get("knowledge_trust", 1.0) > 0.8:
            risk_downgrades.append("downgrade")

        risk_level = current_risk
        if risk_upgrades and not risk_downgrades:
            # Upgrade risk level
            upgrade_map = {
                "Very Low": "Low",
                "Low": "Medium",
                "Medium": "High",
                "High": "Critical",
            }
            risk_level = upgrade_map.get(risk_level, risk_level)
        elif risk_downgrades and not risk_upgrades:
            # Downgrade risk level
            downgrade_map = {
                "Critical": "High",
                "High": "Medium",
                "Medium": "Low",
                "Low": "Very Low",
            }
            risk_level = downgrade_map.get(risk_level, risk_level)

        return risk_level

    def fuse(
        self, inputs: SignalInputs, thresholds: Optional[DecisionThresholds] = None
    ) -> FusionResult:
        """Fuse all evidence and produce a decision result."""
        t = thresholds or self.thresholds
        weighted_score = self.compute_weighted_score(inputs)

        classification, risk_level, confidence = self.classify(weighted_score, t)

        # Identify conflicting evidence
        conflicting = self._detect_conflicts(inputs)

        # Build signal breakdown
        breakdown = self._compute_signal_breakdown(inputs)

        return FusionResult(
            classification=classification,
            risk_level=risk_level,
            confidence=confidence,
            weighted_score=weighted_score,
            contributing_signals=self._extract_contributing_signals(inputs),
            conflicting_evidence=conflicting,
            signal_breakdown=breakdown,
        )

    def _detect_conflicts(self, inputs: SignalInputs) -> List[Dict[str, Any]]:
        """Detect conflicting evidence across subsystems."""
        conflicts = []

        # High ML confidence but low retrieval confidence
        ml_conf = inputs.ml.get("confidence", 0)
        retr_conf = inputs.retrieval.get("confidence", 0)
        if ml_conf > 0.7 and retr_conf < 0.3:
            conflicts.append(
                {
                    "type": "ml_vs_retrieval",
                    "description": "High ML confidence but low retrieval confidence",
                    "ml_confidence": ml_conf,
                    "retrieval_confidence": retr_conf,
                }
            )

        # High retrieval but uncertain LLM
        retr_conf = inputs.retrieval.get("confidence", 0)
        llm_conf = inputs.llm.get("confidence", 0)
        if retr_conf > 0.7 and llm_conf < 0.3:
            conflicts.append(
                {
                    "type": "retrieval_vs_llm",
                    "description": "High retrieval confidence but uncertain LLM",
                    "retrieval_confidence": retr_conf,
                    "llm_confidence": llm_conf,
                }
            )

        # Strong manipulation but message appears legitimate
        manipulation = inputs.llm.get("manipulation_detected", False)
        semantic_conf = inputs.semantic.get("confidence", 0)
        if manipulation and semantic_conf > 0.6:
            conflicts.append(
                {
                    "type": "manipulation_vs_legitimate",
                    "description": "Strong manipulation detected but message appears legitimate",
                    "manipulation_detected": manipulation,
                    "semantic_confidence": semantic_conf,
                }
            )

        # Conflicting knowledge documents
        retr_knowledge = retr_conf * inputs.retrieval.get("knowledge_trust", 0.5)
        if retr_knowledge < 0.3:
            conflicts.append(
                {
                    "type": "low_knowledge_trust",
                    "description": "Low knowledge document trust score",
                    "knowledge_trust": retr_knowledge,
                }
            )

        # Low semantic confidence
        if semantic_conf := inputs.semantic.get("confidence", 0) < 0.3:
            conflicts.append(
                {
                    "type": "low_semantic_confidence",
                    "description": "Low semantic understanding confidence",
                    "semantic_confidence": semantic_conf,
                }
            )

        return conflicts

    def _compute_signal_breakdown(
        self, inputs: SignalInputs
    ) -> Dict[str, Dict[str, float]]:
        """Compute per-signal breakdown details."""
        breakdown = {}
        for sig_name in [
            "semantic",
            "intent",
            "behavior",
            "retrieval",
            "llm",
            "ml",
            "historical",
            "entities",
        ]:
            data = getattr(inputs, sig_name)
            breakdown[sig_name] = {
                "raw_score": self.normalize_signal(sig_name, data),
                "weight": getattr(self.normalized_weights, f"{sig_name}_weight", 1.0),
                "confidence": data.get("confidence", 0.0),
            }
        return breakdown

    def _extract_contributing_signals(self, inputs: SignalInputs) -> Dict[str, float]:
        """Extract the contributing score from each signal."""
        contributing = {}
        for sig_name in [
            "semantic",
            "intent",
            "behavior",
            "retrieval",
            "llm",
            "ml",
            "historical",
            "entities",
        ]:
            score = self.normalize_signal(sig_name, getattr(inputs, sig_name))
            contributing[sig_name] = score
        return contributing
