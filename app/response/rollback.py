"""Rollback support."""

from __future__ import annotations
from .models import ActionStep, ActionState
from app.core.logging import get_logger

logger = get_logger(__name__)


class RollbackManager:
    def rollback(self, step: ActionStep) -> ActionStep:
        if not step.rollback_supported:
            logger.warning("Rollback not supported for %s", step.action_id)
            step.status = ActionState.FAILED
            return step
        step.status = ActionState.ROLLED_BACK
        logger.info("Rolled back action %s", step.action_id)
        return step
