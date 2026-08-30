from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from .models import LookupRequest, LookupResult


class Executor:
    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_single(self, func, *args, **kwargs):
        async with self._semaphore:
            return await func(*args, **kwargs)

    async def execute_many(self, tasks: List) -> List:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results