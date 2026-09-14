"""Rate limiting."""

from __future__ import annotations

from collections import deque
from time import time

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.clients: dict[str, deque] = {}

    def allow(self, client_id: str) -> bool:
        now = time()
        q = self.clients.setdefault(client_id, deque())
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True
