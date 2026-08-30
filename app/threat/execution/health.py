from __future__ import annotations

from .metrics import ExecutionMetrics


class HealthChecker:
    def __init__(self, metrics: ExecutionMetrics):
        self.metrics = metrics

    def check(self) -> Dict:
        s = self.metrics.summary()
        total = s.get("total_requests", 0)
        successes = sum(s.get("provider_success", {}).values())
        failures = sum(s.get("provider_failure", {}).values())
        timeouts = s.get("total_timeouts", 0)
        return {
            "total_requests": total,
            "successes": successes,
            "failures": failures,
            "timeouts": timeouts,
            "availability": successes / total if total else 1.0,
        }