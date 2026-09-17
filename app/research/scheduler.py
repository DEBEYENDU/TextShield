"""Research scheduler."""

from __future__ import annotations
from typing import List
from .models import ResearchRequest
from datetime import datetime, timedelta

class ResearchScheduler:
    def __init__(self):
        self.queue: List[ResearchRequest] = []

    def schedule(self, req: ResearchRequest) -> None:
        self.queue.append(req)

    def next_due(self) -> ResearchRequest | None:
        if not self.queue:
            return None
        self.queue.sort(key=lambda r: r.priority, reverse=True)
        return self.queue.pop(0)
