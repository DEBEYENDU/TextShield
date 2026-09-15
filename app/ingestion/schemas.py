"""Normalized message ingestion schemas."""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class IngestionMessage(BaseModel):
    message: str = Field(..., description="Message content")
    source: str = Field(default="api", description="Source of ingestion")
    channel: str = Field(default="unknown", description="Channel type")
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: Optional[str] = None
    external_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
