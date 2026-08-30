from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List


@dataclass
class LookupRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ioc: str = ""
    ioc_type: str = ""
    providers: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    duration: Optional[float] = None
    result: Optional[dict] = None


@dataclass
class LookupResult:
    request_id: str = ""
    completed_providers: Dict[str, any] = field(default_factory=dict)
    failed_providers: Dict[str, any] = field(default_factory=dict)
    timed_out_providers: List[str] = field(default_factory=list)
    retries_total: int = 0
    partial: bool = False