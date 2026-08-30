from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Callable, Optional


class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_backoff: float = 1.0,
                 max_backoff: float = 60.0, jitter: bool = True):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.jitter = jitter

    async def retry(self, func: Callable, *args, **kwargs) -> Optional:
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff = self.base_backoff * (2 ** attempt)
                    if self.jitter:
                        backoff += random.uniform(0, 1)
                    backoff = min(backoff, self.max_backoff)
                    await asyncio.sleep(backoff)
                else:
                    break
        raise last_exception


class ExponentialBackoff:
    def __init__(self, base: float = 1.0, multiplier: float = 2.0, max_delay: float = 60.0, jitter: bool = True):
        self.base = base
        self.multiplier = multiplier
        self.max_delay = max_delay
        self.jitter = jitter

    def calculate(self, attempt: int) -> float:
        delay = self.base * (self.multiplier ** attempt)
        if self.jitter:
            delay += random.uniform(0, 1)
        return min(delay, self.max_delay)