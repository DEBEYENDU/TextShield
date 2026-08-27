from __future__ import annotations

import asyncio
import time
from collections import deque, defaultdict
from threading import Lock
from typing import Any, Dict, Deque, Optional, Tuple

from .providers.threat_indicator import ThreatIndicator

logger = logging.getLogger(__name__)


class RateLimitManager:
    """Provider-aware rate limiting for threat intelligence providers.
    
    Supports:
    - Burst limits
    - Daily quotas
    - Retries with exponential backoff
    - Priority queue
    - Provider cooldown
    """
    
    def __init__(self):
        """Initialize the rate limit manager."""
        # Per-provider rate limits: {provider: {"burst": int, "period": int, "used": int, "last_reset": float}}
        self._limits: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"burst": 10, "period": 60, "used": 0, "last_reset": time.time()}
        )
        # Per-provider daily quotas: {provider: {"daily": int, "used_today": int, "last_reset_date": str}}
        self._daily_quotas: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"daily": 1000, "used_today": 0, "last_reset_date": datetime.utcnow().strftime("%Y-%m-%d")}
        )
        # Cooldown tracking: {provider: last_usage_time}
        self._cooldowns: Dict[str, float] = {}
        # Global rate limit
        self._global_limit: Dict[str, Any] = {"burst": 100, "period": 60, "used": 0, "last_reset": time.time()}
        # Lock for thread safety
        self._lock = Lock()
    
    def set_provider_limit(self, provider: str, burst: int, period: int) -> None:
        """Set rate limit for a specific provider.
        
        Args:
            provider: Provider name
            burst: Maximum requests in the burst period
            period: Time period in seconds
        """
        with self._lock:
            self._limits[provider] = {
                "burst": burst,
                "period": period,
                "used": 0,
                "last_reset": time.time(),
            }
    
    def set_daily_quota(self, provider: str, daily: int) -> None:
        """Set daily quota for a specific provider.
        
        Args:
            provider: Provider name
            daily: Maximum requests per day
        """
        with self._lock:
            self._daily_quotas[provider] = {
                "daily": daily,
                "used_today": 0,
                "last_reset_date": datetime.utcnow().strftime("%Y-%m-%d"),
            }
    
    def check_rate_limit(
        self,
        provider: str,
        allow_burst: bool = True,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if a request is within rate limits.
        
        Args:
            provider: Provider name
            allow_burst: Whether burst requests are allowed
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        with self._lock:
            limit_info = self._limits.get(provider, self._limits["default"])
            daily_info = self._daily_quotas.get(provider, self._daily_quotas["default"])
            
            now = time.time()
            elapsed = now - limit_info["last_reset"]
            
            # Check period reset
            if elapsed >= limit_info["period"]:
                limit_info["used"] = 0
                limit_info["last_reset"] = now
            
            # Check daily reset
            today = datetime.utcnow().strftime("%Y-%m-%d")
            if daily_info["last_reset_date"] != today:
                daily_info["used_today"] = 0
                daily_info["last_reset_date"] = today
            
            # Check daily quota
            daily_allowed = daily_info["used_today"] < daily_info["daily"]
            
            # Check burst/period quota
            period_allowed = (
                limit_info["used"] < limit_info["burst"]
                if allow_burst
                else limit_info["used"] <= limit_info["burst"]
            )
            
            allowed = period_allowed and daily_allowed
            
            info = {
                "provider": provider,
                "allowed": allowed,
                "burst_limit": limit_info["burst"],
                "burst_used": limit_info["used"],
                "burst_remaining": limit_info["burst"] - limit_info["used"],
                "period": limit_info["period"],
                "daily_limit": daily_info["daily"],
                "daily_used": daily_info["used_today"],
                "daily_remaining": daily_info["daily"] - daily_info["used_today"],
                "reset_in": max(0, limit_info["period"] - int(elapsed)),
                "daily_reset_in": max(
                    0, 
                    (datetime.strptime(daily_info["last_reset_date"], "%Y-%m-%d")
                     .replace(hour=23, minute=59, second=59)
                     .timestamp() - now)
                ),
            }
            
            if allowed:
                limit_info["used"] += 1
                daily_info["used_today"] += 1
            
            return allowed, info
    
    async def wait_for_rate_limit(
        self,
        provider: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until rate limit allows a request.
        
        Args:
            provider: Provider name
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if allowed within timeout, False otherwise
        """
        start = time.time()
        while True:
            allowed, info = self.check_rate_limit(provider)
            if allowed:
                return True
            
            reset_in = info.get("reset_in", 0)
            if timeout and (time.time() - start) > timeout:
                return False
            
            # Wait before checking again
            await asyncio.sleep(min(reset_in, 1.0))
    
    def record_usage(self, provider: str, count: int = 1) -> None:
        """Record usage after a successful request.
        
        Args:
            provider: Provider name
            count: Number of requests to record
        """
        with self._lock:
            if provider in self._limits:
                self._limits[provider]["used"] += count
    
    def set_cooldown(self, provider: str, duration: int) -> None:
        """Set cooldown period for a provider.
        
        Args:
            provider: Provider name
            duration: Cooldown duration in seconds
        """
        with self._lock:
            self._cooldowns[provider] = time.time() + duration
    
    def is_on_cooldown(self, provider: str) -> bool:
        """Check if a provider is on cooldown.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is on cooldown
        """
        with self._lock:
            if provider not in self._cooldowns:
                return False
            return time.time() > self._cooldowns[provider]
    
    def get_status(self) -> Dict[str, Any]:
        """Get rate limit status for all providers."""
        with self._lock:
            status = {}
            for provider, limit in self._limits.items():
                elapsed = time.time() - limit["last_reset"]
                status[provider] = {
                    "burst_limit": limit["burst"],
                    "burst_used": limit["used"],
                    "burst_remaining": max(0, limit["burst"] - limit["used"]),
                    "period": limit["period"],
                    "elapsed": int(elapsed),
                    "reset_in": max(0, limit["period"] - int(elapsed)),
                    "daily": self._daily_quotas.get(
                        provider, {"daily": 1000, "used_today": 0}
                    ),
                }
            return status