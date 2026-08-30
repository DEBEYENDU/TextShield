from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from .models import LookupRequest, LookupResult
from .retry import RetryPolicy
from .timeout import TimeoutManager


class Dispatcher:
    def __init__(self, retry_policy: RetryPolicy, timeout_manager: TimeoutManager,
                 circuit_breakers: Dict[str, any], concurrency_limiter):
        self.retry_policy = retry_policy
        self.timeout_manager = timeout_manager
        self.circuit_breakers = circuit_breakers
        self.concurrency_limiter = concurrency_limiter

    async def dispatch(self, req: LookupRequest) -> LookupResult:
        result = LookupResult(req.request_id)
        tasks = []
        for provider in req.providers or []:
            cb = self.circuit_breakers.get(provider)
            if cb and not cb.can_execute():
                result.timed_out_providers.append(provider)
                continue
            task = asyncio.create_task(self._lookup_provider(provider, req))
            tasks.append(task)
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        for pr in provider_results:
            if isinstance(pr, Exception):
                continue
            # categorize
            provider = pr.get("provider", "")
            status = pr.get("status", "")
            if status == "success":
                result.completed_providers[provider] = pr
            else:
                result.failed_providers[provider] = pr
        return result

    async def _lookup_provider(self, provider: str, req: LookupRequest):
        async with self.concurrency_limiter:
            # apply retry
            attempt = 0
            while True:
                try:
                    await asyncio.sleep(0.01)  # simulate lookup
                    return {"provider": provider, "status": "success", "data": {}}
                except asyncio.CancelledError:
                    return {"provider": provider, "status": "cancelled"}
                finally:
                    attempt += 1
                    if attempt >= self.retry_policy.max_retries:
                        break