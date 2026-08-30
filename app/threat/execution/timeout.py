from __future__ import annotations

import asyncio
from typing import Optional, Callable


class TimeoutError(Exception):
    pass


class TimeoutManager:
    def __init__(self, global_timeout: Optional[float] = None, provider_timeout: Optional[float] = None):
        self.global_timeout = global_timeout
        self.provider_timeout = provider_timeout

    async def run_with_timeout(self, coro, timeout: Optional[float] = None):
        t = timeout or self.provider_timeout or self.global_timeout
        if t is None:
            return await coro
        return await asyncio.wait_for(coro, timeout=t)