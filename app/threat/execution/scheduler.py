from __future__ import annotations

import asyncio
import heapq
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import LookupRequest


class Scheduler:
    def __init__(self, high_priority_weight: float = 2.0):
        self._normal_queue: List[Tuple[datetime, LookupRequest]] = []
        self._high_queue: List[Tuple[datetime, LookupRequest]] = []
        self._high_weight = high_priority_weight
        self._counter = 0

    def submit(self, request: LookupRequest, priority: str = "normal") -> None:
        now = datetime.now(timezone.utc)
        entry = (now, request)
        if priority == "high":
            heapq.heappush(self._high_queue, entry)
        else:
            heapq.heappush(self._normal_queue, entry)

    def next_request(self) -> Optional[LookupRequest]:
        # high priority first
        if self._high_queue:
            _, req = heapq.heappop(self._high_queue)
            return req
        if self._normal_queue:
            _, req = heapq.heappop(self._normal_queue)
            return req
        return None

    def size(self) -> int:
        return len(self._high_queue) + len(self._normal_queue)