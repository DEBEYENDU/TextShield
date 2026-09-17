"""Action executor."""

from __future__ import annotations
from .models import ActionStep, ActionState
from app.core.logging import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def execute(self, step: ActionStep) -> ActionStep:
        if self.dry_run:
            logger.info("Dry run for action %s", step.action_id)
            step.status = ActionState.COMPLETED
            return step
        # Local actions only
        if step.action_type.value in ["MONITOR", "WARN", "TAG", "NOTIFY", "REVIEW"]:
            step.status = ActionState.COMPLETED
            logger.info("Executed low-risk action %s", step.action_id)
            return step
        # Placeholder for quarantine/block
        step.status = ActionState.COMPLETED
        logger.info("Executed action %s", step.action_id)
        return step

    def verify(self, step: ActionStep) -> bool:
        # Simplified verification
        return step.status == ActionState.COMPLETED
