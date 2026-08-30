from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, List


class ExecutionMetrics:
    def __init__(self):
        self.requests: List[Dict] = []
        self.provider_success: Counter = Counter()
        self.provider_failure: Counter = Counter()
        self.provider_timeout: Counter = Counter()
        self.total_requests = 0
        self.total_retries = 0
        self.total_timeouts = 0
        self.total_duration: float = 0.0

    def record(self, request_id: str, duration: float, success: bool,
               providers: List[str], timed_out: List[str] = None,
               retries: int = 0):
        self.total_requests += 1
        self.total_duration += duration
        self.total_retries += retries
        if timed_out:
            self.total_timeouts += len(timed_out)
        if success:
            for p in providers:
                self.provider_success[p] += 1
        else:
            for p in providers:
                self.provider_failure[p] += 1
        self.requests.append({
            "id": request_id,
            "duration": duration,
            "success": success,
            "providers": providers,
            "retries": retries,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def summary(self) -> Dict:
        total = self.total_requests
        avg_duration = self.total_duration / total if total else 0.0
        return {
            "total_requests": total,
            "average_duration": avg_duration,
            "total_retries": self.total_retries,
            "total_timeouts": self.total_timeouts,
            "provider_success": dict(self.provider_success),
            "provider_failure": dict(self.provider_failure),
            "provider_timeout": dict(self.provider_timeout),
        }