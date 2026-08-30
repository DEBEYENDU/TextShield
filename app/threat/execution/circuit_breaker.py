from __future__ import annotations

import asyncio
import random
from enum import Enum
from typing import Dict, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._failures = 0
        self._successes = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._call_count = 0

    def record_success(self):
        self._call_count += 1
        self._successes += 1
        if self._state == CircuitState.HALF_OPEN and self._successes >= self.success_threshold:
            self._reset()

    def record_failure(self):
        self._call_count += 1
        self._failures += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        if self._state == CircuitState.CLOSED and self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._failures = 0

    def _reset(self):
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._last_failure_time = None
        self._last_success_time = asyncio.get_event_loop().time()

    def can_execute(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            return False
        if self._state == CircuitState.HALF_OPEN:
            return True
        return False

    async def wait_for_reset(self):
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = asyncio.get_event_loop().time() - self._last_failure_time
            if elapsed < self.recovery_timeout:
                await asyncio.sleep(self.recovery_timeout - elapsed)