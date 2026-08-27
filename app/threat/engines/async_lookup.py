from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from .cache import ThreatCache
from .engines.aggregator import ReputationAggregator
from .ioc import IOCType, IOCExtractor
from .providers.threat_indicator import ThreatIndicator

logger = logging.getLogger(__name__)


class AsyncLookupService:
    """Asynchronous threat intelligence lookup service.
    
    Executes provider lookups concurrently with proper:
    - Timeout handling
    - Retry logic
    - Circuit breaker pattern
    - Partial result support
    - Graceful degradation
    """
    
    def __init__(
        self,
        cache: Optional[ThreatCache] = None,
        aggregator: Optional[ReputationAggregator] = None,
        rate_limit_manager: Optional[Any] = None,
        max_concurrent: int = 5,
        default_timeout: float = 5.0,
        max_retries: int = 3,
    ):
        """Initialize the async lookup service.
        
        Args:
            cache: ThreatCache instance
            aggregator: ReputationAggregator instance
            rate_limit_manager: RateLimitManager instance
            max_concurrent: Maximum concurrent lookups
            default_timeout: Default timeout per provider in seconds
            max_retries: Maximum retry attempts
        """
        self.cache = cache or ThreatCache()
        self.aggregator = aggregator or ReputationAggregator()
        self.rate_limit_manager = rate_limit_manager
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def lookup(
        self,
        ioc_value: str,
        ioc_type: IOCType,
        provider_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Perform asynchronous threat intelligence lookup for an IOC.
        
        Args:
            ioc_value: The IOC value (URL, domain, IP, etc.)
            ioc_type: Type of IOC (URL, domain, IP, email, etc.)
            provider_names: Specific providers to query (None = all enabled)
            
        Returns:
            Lookup results dict with indicators, aggregation, and metadata
        """
        # Check cache first
        cached = await self.cache.async_get(ioc_value)
        if cached:
            return {
                "ioc_value": ioc_value,
                "ioc_type": ioc_type.value,
                "from_cache": True,
                "indicators": [cached.to_dict()],
                "aggregated": False,
            }
        
        # Determine which providers to query
        if provider_names is None:
            provider_names = self._get_enabled_provider_names()
        
        # Semaphore-limited concurrent lookups
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Execute lookups concurrently
        tasks = []
        for provider_name in provider_names:
            task = self._lookup_with_semaphore(
                semaphore,
                provider_name,
                ioc_value,
                ioc_type,
            )
            tasks.append(task)
        
        # Wait for all lookups (with timeout)
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=self.default_timeout * len(provider_names),
        )
        
        # Process results
        valid_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result is not None:
                valid_results.append(result)
        
        # Cache results
        if valid_results:
            for indicator in valid_results:
                await self.cache.async_set(ioc_value, indicator, indicator.provider)
        
        # Aggregate reputation
        aggregated = {}
        if valid_results:
            agg_result = await self.aggregator.aggregate(valid_results, provider_names)
            aggregated = agg_result
        
        return {
            "ioc_value": ioc_value,
            "ioc_type": ioc_type.value,
            "from_cache": False,
            "indicators": [ind.to_dict() for ind in valid_results],
            "aggregated": bool(aggregated),
            "aggregation": aggregated,
            "errors": errors,
            "provider_count": len(provider_names),
            "successful_providers": len(valid_results),
        }
    
    async def _lookup_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        provider_name: str,
        ioc_value: str,
        ioc_type: IOCType,
    ) -> Optional[ThreatIndicator]:
        """Execute a single provider lookup with semaphore control."""
        async with semaphore:
            return await self._lookup_provider(provider_name, ioc_value, ioc_type)
    
    async def _lookup_provider(
        self,
        provider_name: str,
        ioc_value: str,
        ioc_type: IOCType,
    ) -> Optional[ThreatIndicator]:
        """Look up threat intelligence from a single provider.
        
        Includes retry logic, timeout, and circuit breaker support.
        """
        from .providers import ThreatProviderABC
        
        # Check rate limit
        if self.rate_limit_manager:
            allowed, _ = self.rate_limit_manager.check_rate_limit(provider_name)
            if not allowed:
                logger.warning(f"Rate limit exceeded for provider: {provider_name}")
                return None
        
        # Get the provider from the global registry
        from . import get_threat_registry
        registry = get_threat_registry()
        provider = registry.get(provider_name)
        
        if not provider:
            logger.error(f"Provider not found: {provider_name}")
            return None
        
        # Check cooldown
        if self.rate_limit_manager and self.rate_limit_manager.is_on_cooldown(provider_name):
            logger.warning(f"Provider on cooldown: {provider_name}")
            return None
        
        # Execute lookup with retries
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Execute the appropriate lookup method based on IOC type
                if hasattr(provider, f"lookup_{ioc_type.value}"):
                    method = getattr(provider, f"lookup_{ioc_type.value}")
                elif hasattr(provider, "lookup_url"):
                    method = provider.lookup_url
                elif hasattr(provider, "lookup_domain"):
                    method = provider.lookup_domain
                elif hasattr(provider, "lookup_ip"):
                    method = provider.lookup_ip
                else:
                    logger.warning(f"No lookup method for IOC type: {ioc_type}")
                    return None
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    method(ioc_value),
                    timeout=self.default_timeout,
                )
                
                # Reset error count on success
                if self.rate_limit_manager:
                    self.rate_limit_manager.record_usage(provider_name)
                
                # Check if result is valid
                if result and isinstance(result, ThreatIndicator):
                    # Update provider cooldown
                    if self.rate_limit_manager:
                        self.rate_limit_manager.set_cooldown(provider_name, 60)
                    return result
                
                # If result is something unexpected, continue
                logger.warning(f"Unexpected result from {provider_name}: {type(result)}")
                last_error = Exception(f"Unexpected result type from {provider_name}")
                continue
                
            except asyncio.TimeoutError:
                last_error = Exception(f"Timeout from provider {provider_name} (attempt {attempt + 1})")
                logger.warning(f"Timeout from {provider_name} (attempt {attempt + 1})")
                
            except Exception as e:
                last_error = e
                logger.warning(f"Error from {provider_name} (attempt {attempt + 1}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                backoff = min(2 ** attempt, 10)  # Max 10 second backoff
                await asyncio.sleep(backoff)
        
        # All retries exhausted
        logger.error(f"All {self.max_retries + 1} attempts failed for {provider_name}: {last_error}")
        
        # Record cooldown on failure
        if self.rate_limit_manager:
            self.rate_limit_manager.set_cooldown(provider_name, 120)
        
        return None
    
    def _get_enabled_provider_names(self) -> List[str]:
        """Get names of all enabled providers."""
        from . import get_threat_registry
        registry = get_threat_registry()
        return [name for name, provider in registry.get_all().items() if provider.enabled]
    
    async def batch_lookup(
        self,
        iocs: List[Tuple[str, IOCType]],
        provider_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform batch asynchronous lookups for multiple IOCs.
        
        Args:
            iocs: List of (ioc_value, ioc_type) tuples
            provider_names: Specific providers to query
            
        Returns:
            List of lookup results
        """
        results = []
        for ioc_value, ioc_type in iocs:
            result = await self.lookup(ioc_value, ioc_type, provider_names)
            results.append(result)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "default_timeout": self.default_timeout,
            "max_retries": self.max_retries,
            "cache_stats": self.cache.get_stats(),
            "aggregator_weights": self.aggregator.get_weights(),
        }