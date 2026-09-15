"""Approval workflow."""

from __future__ import annotations
from .models import Approval, ActionStep, ActionState
from app.core.logging import get_logger

logger = get_logger(__name__)


class ApprovalWorkflow:
    def __init__(self):
        self.approvals = {}

    def require_approval(self, step: ActionStep) -> bool:
        return step.approval_required

    def approve(self, step: ActionStep, approver: str, reason: str = "") -> Approval:
        approval = Approval(
            approval_id=f"appr:{step.action_id}",
            action_id=step.action_id,
            approver=approver,
            decision="APPROVED",
            reason=reason
        )
        step.status = ActionState.APPROVED
        self.approvals[step.action_id] = approval
        logger.info("Action %s approved by %s", step.action_id, approver)
        return approval

    def reject(self, step: ActionStep, approver: str, reason: str = "") -> Approval:
        approval = Approval(
            approval_id=f"appr:{step.action_id}",
            action_id=step.action_id,
            approver=approver,
            decision="REJECTED",
            reason=reason
        )
        step.status = ActionState.REJECTED
        self.approvals[step.action_id] = approval
        logger.info("Action %s rejected by %s", step.action_id, approver)
        return approval
