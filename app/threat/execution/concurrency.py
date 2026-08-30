from __future__ import annotations

import asyncio
from typing import Optional, Semaphore


class ConcurrencyLimiter:
    def __init__(self, max_concurrency: int):
        self._semaphore: Semaphore = asyncio.Semaphore(max_concurrency)

    async def acquire(self):
        await self._semaphore.acquire()

    def release(self):
        self._semaphore.release()

    async def run(self, coro):
        async with self._semaphore:
            return await coro