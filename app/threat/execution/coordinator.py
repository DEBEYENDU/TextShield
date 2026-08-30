from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import LookupRequest, LookupResult
from .retry import RetryPolicy
from .timeout import TimeoutManager
from .circuit_breaker import CircuitBreaker, CircuitState


class LookupRequest:
    def __init__(self, ioc: str, ioc_type: str, providers: Optional[List[str]] = None):
        self.request_id = str(uuid.uuid4())
        self.ioc = ioc
        self.ioc_type = ioc_type
        self.providers = providers or []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status: Optional[str] = None
        self.duration: Optional[float] = None
        self.result: Optional[LookupResult] = None


class LookupResult:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.completed_providers: Dict = {}
        self.failed_providers: Dict = {}
        self.timed_out_providers: List[str] = []
        self.retries_total = 0
        self.partial = False


class ThreatCoordinator:
    def __init__(self, retry_policy: RetryPolicy, timeout_manager: TimeoutManager,
                 concurrency_limiter, circuit_breakers: Dict[str, CircuitBreaker]):
        self.retry_policy = retry_policy
        self.timeout_manager = timeout_manager
        self.concurrency_limiter = concurrency_limiter
        self.circuit_breakers = circuit_breakers  # provider -> CircuitBreaker
        self._active_requests: Dict[str, LookupRequest] = {}
        self._metrics = ExecutionMetrics()

    def submit(self, ioc: str, ioc_type: str, providers: Optional[List[str]] = None) -> LookupRequest:
        req = LookupRequest(ioc, ioc_type, providers)
        req.start_time = datetime.now(timezone.utc)
        self._active_requests[req.request_id] = req
        return req

    async def execute(self, req: LookupRequest) -> LookupResult:
        result = LookupResult(req.request_id)
        tasks = []
        for provider in req.providers:
            cb = self.circuit_breakers.get(provider)
            if cb and not cb.can_execute():
                result.timed_out_providers.append(provider)
                continue
            task = self._execute_provider(provider, req)
            tasks.append(task)
        if tasks:
            provider_results = await asyncio.gather(*tasks, return_exceptions=True)
            for pr in provider_results:
                if isinstance(pr, Exception):
                    # categorize failure
                    if "TimeoutError" in type(pr).__name__:
                        # mark timed out
                        pass
                    else:
                        pass
                else:
                    # collect success
                    pass
        req.end_time = datetime.now(timezone.utc)
        req.duration = (req.end_time - req.start_time).total_seconds()
        req.status = "completed"
        req.result = result
        self._metrics.record(
            req.request_id, req.duration,
            result is not None,
            list(result.completed_providers.keys()) if result else [],
            timed_out=list(result.timed_out_providers),
            retries=self.retry_policy.max_retries if result else 0,
        )
        self._active_requests.pop(req.request_id, None)
        return result

    async def _execute_provider(self, provider: str, req: LookupRequest):
        cb = self.circuit_breakers.get(provider)
        if cb:
            if not cb.can_execute():
                return {"provider": provider, "status": "circuit_open", "status_code": None}
            cb.record_success()
        # simulate work
        await asyncio.sleep(0.01)
        return {"provider": provider, "status": "success", "data": {}}