"""Provider-aware rate limiting: per-minute / per-day quotas.

When limits are reached the caller receives a verdict of "unavailable"
with status "rate_limited" (or a cached result) — analysis never crashes.
"""

from __future__ import annotations

import time
from collections import deque

from app.threat_intel.exceptions import RateLimitExceededError


class ProviderRateLimiter:
    """Sliding-window rate limiter keyed by provider name."""

    def __init__(self, limits: dict[str, tuple[int, int]] | None = None):
        # provider -> (per_minute, per_day); 0 means unlimited
        self.limits = limits or {}
        self._minute_hits: dict[str, deque] = {}
        self._day_hits: dict[str, deque] = {}
        self.limited_events = 0

    def configure(self, provider: str, per_minute: int, per_day: int) -> None:
        self.limits[provider] = (per_minute, per_day)

    def _prune(self, queue: deque, window: float, now: float) -> None:
        while queue and now - queue[0] > window:
            queue.popleft()

    def check(self, provider: str) -> None:
        """Raise RateLimitExceededError when the provider is over quota."""
        per_minute, per_day = self.limits.get(provider, (0, 0))
        if not per_minute and not per_day:
            return
        now = time.time()
        minute_q = self._minute_hits.setdefault(provider, deque())
        day_q = self._day_hits.setdefault(provider, deque())
        self._prune(minute_q, 60.0, now)
        self._prune(day_q, 86400.0, now)
        if (per_minute and len(minute_q) >= per_minute) or \
                (per_day and len(day_q) >= per_day):
            self.limited_events += 1
            raise RateLimitExceededError(
                f"provider '{provider}' exceeded quota "
                f"({per_minute}/min, {per_day}/day)")

    def record(self, provider: str) -> None:
        now = time.time()
        self._minute_hits.setdefault(provider, deque()).append(now)
        self._day_hits.setdefault(provider, deque()).append(now)

    def allow(self, provider: str) -> bool:
        """Non-raising check used before attempting a lookup."""
        try:
            self.check(provider)
            return True
        except RateLimitExceededError:
            return False

    def stats(self) -> dict:
        return {"limited_events": self.limited_events,
                "tracked_providers": sorted(self._minute_hits)}
