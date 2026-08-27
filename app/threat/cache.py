from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from .ioc import IOCType, IOCExtractor, ExtractedIOC, ExtractedIOC
from .providers.threat_indicator import ThreatIndicator

logger = logging.getLogger(__name__)


class ThreatCache:
    """Intelligent caching for threat intelligence lookups.
    
    Features:
    - TTL-based expiration
    - Automatic refresh
    - Cache invalidation
    - Provider-specific TTL
    - Background refresh
    - Memory + optional persistent storage
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 10000):
        """Initialize the threat cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            max_size: Maximum number of cached entries
        """
        self.default_ttl: int = default_ttl
        self.max_size: int = max_size
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._provider_ttls: Dict[str, int] = {}
        self._initialized: bool = False
    
    def _ensure_init(self) -> None:
        """Ensure cache is initialized."""
        if not self._initialized:
            self._initialized = True
    
    def set_provider_ttl(self, provider: str, ttl: int) -> None:
        """Set provider-specific TTL."""
        self._provider_ttls[provider] = ttl
    
    def get_ttl(self, provider: str) -> int:
        """Get TTL for a provider, falls back to default."""
        return self._provider_ttls.get(provider, self.default_ttl)
    
    def get(
        self,
        key: str,
        provider: Optional[str] = None,
    ) -> Optional[ThreatIndicator]:
        """Get a cached threat indicator.
        
        Args:
            key: Cache key (typically the IOC value)
            provider: Optional provider name for provider-specific TTL
            
        Returns:
            Cached ThreatIndicator or None if not found/expired
        """
        self._ensure_init()
        
        if key not in self._memory_cache:
            return None
        
        entry = self._memory_cache[key]
        
        # Check expiration
        entry_ttl = self.get_ttl(provider) if provider else self.default_ttl
        elapsed = time.time() - entry.get("cached_at", 0)
        
        if elapsed > entry_ttl:
            # Expired - remove it
            del self._memory_cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None
        
        # Update access time
        self._access_times[key] = time.time()
        
        # Refresh TTL on access (optional - extend TTL)
        entry["cached_at"] = time.time()
        
        # Parse back to ThreatIndicator
        try:
            from datetime import datetime
            indicator = ThreatIndicator.from_dict(entry)
            return indicator
        except Exception:
            # Corrupted entry - remove it
            del self._memory_cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None
    
    def set(
        self,
        key: str,
        indicator: ThreatIndicator,
        provider: Optional[str] = None,
    ) -> None:
        """Cache a threat indicator.
        
        Args:
            key: Cache key (typically the IOC value)
            indicator: ThreatIndicator to cache
            provider: Optional provider name for provider-specific TTL
        """
        self._ensure_init()
        
        # Enforce max size using LRU-like approach
        if len(self._memory_cache) >= self.max_size and key not in self._memory_cache:
            # Remove least recently accessed entry
            oldest_key = min(self._access_times, key=self._access_times.get)
            del self._memory_cache[oldest_key]
            if oldest_key in self._access_times:
                del self._access_times[oldest_key]
        
        # Store the indicator
        entry = indicator.to_dict()
        entry["cached_at"] = time.time()
        
        self._memory_cache[key] = entry
        self._access_times[key] = time.time()
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was found and removed
        """
        if key in self._memory_cache:
            del self._memory_cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return True
        return False
    
    def invalidate_provider(self, provider: str) -> int:
        """Invalidate all cache entries for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Number of entries removed
        """
        removed = 0
        keys_to_remove = [
            key for key in self._memory_cache
            if self._memory_cache[key].get("provider") == provider
        ]
        for key in keys_to_remove:
            self.invalidate(key)
            removed += 1
        return removed
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache = {}
        self._access_times = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._memory_cache),
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
            "miss_rate": 1.0 - self._calculate_hit_rate() if self._memory_cache else 0.0,
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)."""
        if not self._access_times:
            return 0.0
        # Simple ratio of accessed entries to total
        accessed = len(self._access_times)
        total = len(self._memory_cache)
        return accessed / total if total > 0 else 0.0
    
    async def async_get(self, key: str, provider: Optional[str] = None) -> Optional[ThreatIndicator]:
        """Asynchronously get a cached threat indicator."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get, key, provider)
    
    async def async_set(self, key: str, indicator: ThreatIndicator, provider: Optional[str] = None) -> None:
        """Asynchronously set a cached threat indicator."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.set, key, indicator, provider)