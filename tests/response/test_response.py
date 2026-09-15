"""Tests for response engine."""

from app.response.decision import ResponseDecider
from app.response.models import PolicyType, ActionType
from app.response.policy_engine import PolicyEngine
from app.response.executor import ActionExecutor
from app.response.approval import ApprovalWorkflow
from app.response.models import ActionStep, ResponseScope


def test_policy_engine():
    engine = PolicyEngine()
    res = engine.evaluate(PolicyType.CONSERVATIVE, "PHISHING", "HIGH", 0.9)
    assert res["action"] == ActionType.QUARANTINE


def test_response_decider():
    decider = ResponseDecider()
    decision = decider.decide("a1", "d1", "PHISHING", "HIGH", 0.9, PolicyType.CONSERVATIVE)
    assert decision.action == ActionType.QUARANTINE
    assert decision.requires_approval is True


def test_executor_dry_run():
    execu = ActionExecutor(dry_run=True)
    step = ActionStep(action_id="s1", sequence=1, action_type=ActionType.WARN, target="msg1", scope=ResponseScope.MESSAGE)
    result = execu.execute(step)
    assert result.status.value == "COMPLETED"


def test_approval():
    wf = ApprovalWorkflow()
    step = ActionStep(action_id="s2", sequence=1, action_type=ActionType.QUARANTINE, target="msg2", scope=ResponseScope.MESSAGE, approval_required=True)
    approval = wf.approve(step, "admin")
    assert approval.decision == "APPROVED"
    assert step.status.value == "APPROVED"
