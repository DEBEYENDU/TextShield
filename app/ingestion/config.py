"""Ingestion configuration for RFC-012."""

from __future__ import annotations
from pydantic import BaseModel
from app.core.settings import settings


class IngestionConfig(BaseModel):
    queue_backend: str = "local"
    worker_count: int = 2
    max_message_size: int = 5 * 1024 * 1024
    max_batch_size: int = 1000
    job_timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 5
    queue_retention_days: int = 7
    result_retention_days: int = 30
    webhook_timeout: int = 10
    webhook_retries: int = 3
    deduplication_enabled: bool = True
    priority_enabled: bool = True


config = IngestionConfig()
