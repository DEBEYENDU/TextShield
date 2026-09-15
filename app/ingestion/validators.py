"""Input validation for ingestion."""

from __future__ import annotations
from app.ingestion.schemas import IngestionMessage
from app.ingestion.config import config

ALLOWED_CHANNELS = {"email", "sms", "web", "api", "chat", "unknown"}


def validate(message: IngestionMessage) -> dict:
    errors = []
    if not message.message or not message.message.strip():
        errors.append("message is empty")
    if len(message.message) > config.config.max_message_size:
        errors.append("message too large")
    if message.channel not in ALLOWED_CHANNELS:
        errors.append("unsupported channel")
    return {"valid": len(errors) == 0, "errors": errors}
