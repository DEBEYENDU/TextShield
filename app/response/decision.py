"""Response decision engine."""

from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from .models import ResponseDecision, PolicyType, ActionType, ActionReversibility
from .policy_engine import PolicyEngine
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseDecider:
    def __init__(self):
        self.policy_engine = PolicyEngine()

    def decide(self, analysis_id: str, decision_id: str,
               classification: str, risk_level: str, confidence: float,
               policy: PolicyType = PolicyType.CONSERVATIVE,
               attribution_confidence: float = 0.0,
               evidence: list = []) -> ResponseDecision:
        policy_result = self.policy_engine.evaluate(policy, classification, risk_level, confidence, attribution_confidence)
        action = policy_result["action"]
        requires_approval = policy_result.get("requires_approval", False)

        response_id = f"resp:{uuid.uuid4().hex[:12]}"
        decision = ResponseDecision(
            response_id=response_id,
            analysis_id=analysis_id,
            decision_id=decision_id,
            action=action,
            confidence=confidence,
            risk=risk_level,
            policy=policy,
            reason=f"Policy {policy.value} with confidence {confidence:.2f}",
            supporting_evidence=evidence,
            requires_approval=requires_approval,
            reversible=ActionReversibility.REVERSIBLE,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        logger.info("Response decision %s -> %s", response_id, action)
        return decision
