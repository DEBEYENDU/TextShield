"""Request correlation context."""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

_request_ctx: ContextVar[dict] = ContextVar("request_ctx", default={})

@dataclass
class RequestContext:
    request_id: str = field(default_factory=lambda: f"ts-{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    endpoint: str = ""
    method: str = ""
    client_category: str = "unknown"
    analysis_id: str = ""
    model_version: str = ""
    app_version: str = ""

def get_context() -> RequestContext:
    data = _request_ctx.get()
    ctx = RequestContext(**{k: data.get(k, "") for k in RequestContext.__dataclass_fields__})
    return ctx

def set_context(ctx: RequestContext) -> None:
    _request_ctx.set(ctx.__dict__)

def new_request_id() -> str:
    return f"ts-{uuid.uuid4().hex[:12]}"
