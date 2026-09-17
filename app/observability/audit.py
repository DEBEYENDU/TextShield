"""Audit trail."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

AUDIT_PATH = Path("data/audit.log")

def log_event(event_type: str, actor: str, request_id: str, action: str, result: str, metadata: dict | None = None) -> None:
    entry = {
        "ts": time.time(),
        "event_type": event_type,
        "actor": actor,
        "request_id": request_id,
        "action": action,
        "result": result,
        "metadata": metadata or {},
    }
    line = json.dumps(entry)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
