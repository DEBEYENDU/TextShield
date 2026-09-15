"""Security controls for attribution."""

from __future__ import annotations
from .config import config


def validate_access(user_role: str) -> bool:
    allowed = {"admin", "analyst"}
    return user_role.lower() in allowed


def sanitize_output(data: dict) -> dict:
    # remove sensitive fields if benign protection enabled
    if config.benign_protection:
        # placeholder
        pass
    return data
