"""Response policy engine."""

from __future__ import annotations
from .models import PolicyType, ActionType, ActionSafety, ResponseScope
from .config import config
from app.core.logging import get_logger

logger = get_logger(__name__)


class PolicyEngine:
    def __init__(self):
        self.policies = {
            PolicyType.CONSERVATIVE: self._conservative,
            PolicyType.BALANCED: self._balanced,
            PolicyType.AGGRESSIVE: self._aggressive,
        }

    def evaluate(self, policy_type: PolicyType, classification: str, risk_level: str,
                 confidence: float, attribution_confidence: float = 0.0) -> dict:
        func = self.policies.get(policy_type, self._conservative)
        return func(classification, risk_level, confidence, attribution_confidence)

    def _conservative(self, classification: str, risk_level: str,
                      confidence: float, attribution_confidence: float) -> dict:
        if confidence >= 0.85 and risk_level.upper() in ["HIGH", "CRITICAL"] and "PHISH" in classification.upper():
            return {"action": ActionType.QUARANTINE, "requires_approval": True, "safety": ActionSafety.MEDIUM}
        if confidence >= 0.7 and risk_level.upper() in ["MEDIUM", "HIGH"]:
            return {"action": ActionType.REVIEW, "requires_approval": False, "safety": ActionSafety.LOW}
        return {"action": ActionType.MONITOR, "requires_approval": False, "safety": ActionSafety.LOW}

    def _balanced(self, classification: str, risk_level: str,
                  confidence: float, attribution_confidence: float) -> dict:
        if confidence >= 0.9 and risk_level.upper() in ["HIGH", "CRITICAL"]:
            return {"action": ActionType.QUARANTINE, "requires_approval": True, "safety": ActionSafety.MEDIUM}
        if confidence >= 0.75:
            return {"action": ActionType.REVIEW, "requires_approval": False, "safety": ActionSafety.LOW}
        return {"action": ActionType.WARN, "requires_approval": False, "safety": ActionSafety.LOW}

    def _aggressive(self, classification: str, risk_level: str,
                    confidence: float, attribution_confidence: float) -> dict:
        if confidence >= 0.8 and risk_level.upper() in ["HIGH", "CRITICAL"]:
            return {"action": ActionType.QUARANTINE, "requires_approval": False, "safety": ActionSafety.MEDIUM}
        if confidence >= 0.6:
            return {"action": ActionType.REVIEW, "requires_approval": False, "safety": ActionSafety.LOW}
        return {"action": ActionType.MONITOR, "requires_approval": False, "safety": ActionSafety.LOW}
