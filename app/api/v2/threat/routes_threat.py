from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.threat.cache import ThreatCache
from app.threat.engines.aggregator import ReputationAggregator
from app.threat.engines.async_lookup import AsyncLookupService
from app.threat.providers import get_threat_registry
from app.threat.ioc import IOCType, IOCExtractor

router = APIRouter(prefix="/v2/threat", tags=["threat-intelligence"])


# Dependency providers
def get_cache() -> ThreatCache:
    from app.threat import get_threat_system
    from app.threat.cache import ThreatCache
    # Initialize the threat system if needed
    return ThreatCache()


def get_aggregator() -> ReputationAggregator:
    from app.threat import init_aggregator
    return init_aggregator()


def get_lookup_service() -> AsyncLookupService:
    from app.threat import init_threat_system
    from app.threat.engines.async_lookup import AsyncLookupService
    registry = get_threat_registry()
    # Initialize rate limiting for each provider
    return AsyncLookupService()


@router.get("/providers", response_model=Dict[str, Any])
async def list_providers() -> Dict[str, Any]:
    """List all threat intelligence providers."""
    registry = get_threat_registry()
    providers = registry.get_all_metadata()
    enabled = registry.get_enabled()
    
    return {
        "providers": providers,
        "enabled": {name: provider.enabled for name, provider in enabled.items()},
        "total": len(providers),
    }


@router.get("/health", response_model=Dict[str, Any])
async def threat_health() -> Dict[str, Any]:
    """Check threat intelligence provider health."""
    registry = get_threat_registry()
    health = registry.health_check_all()
    
    # Count healthy vs unhealthy
    healthy_count = sum(1 for h in health.values() if h.get("healthy", False))
    unhealthy_count = len(health) - healthy_count
    
    return {
        "providers": health,
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "total": len(health),
    }


@router.post("/url", response_model=Dict[str, Any])
async def analyze_url(
    url: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Analyze a URL for threats using all enabled providers."""
    from app.threat import get_lookup_service
    
    service = get_lookup_service()
    
    # Perform lookup
    result = await service.lookup(url, IOCType.URL)
    
    return {
        "ioc_value": result.get("ioc_value", url),
        "ioc_type": result.get("ioc_type", "url"),
        "from_cache": result.get("from_cache", False),
        "indicators": result.get("indicators", []),
        "aggregated": result.get("aggregated", False),
        "aggregation": result.get("aggregation", {}),
        "errors": result.get("errors", []),
        "successful_providers": result.get("successful_providers", 0),
        "total_providers": result.get("provider_count", 0),
    }


@router.post("/domain", response_model=Dict[str, Any])
async def analyze_domain(
    domain: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Analyze a domain for threats using all enabled providers."""
    from app.threat import get_lookup_service
    
    service = get_lookup_service()
    
    # Perform lookup
    result = await service.lookup(domain, IOCType.DOMAIN)
    
    return {
        "ioc_value": result.get("ioc_value", domain),
        "ioc_type": result.get("ioc_type", "domain"),
        "from_cache": result.get("from_cache", False),
        "indicators": result.get("indicators", []),
        "aggregated": result.get("aggregated", False),
        "aggregation": result.get("aggregation", {}),
        "errors": result.get("errors", []),
        "successful_providers": result.get("successful_providers", 0),
        "total_providers": result.get("provider_count", 0),
    }


@router.post("/ip", response_model=Dict[str, Any])
async def analyze_ip(
    ip: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Analyze an IP address for threats using all enabled providers."""
    from app.threat import get_lookup_service
    
    service = get_lookup_service()
    
    # Perform lookup
    result = await service.lookup(ip, IOCType.IP)
    
    return {
        "ioc_value": result.get("ioc_value", ip),
        "ioc_type": result.get("ioc_type", "ip"),
        "from_cache": result.get("from_cache", False),
        "indicators": result.get("indicators", []),
        "aggregated": result.get("aggregated", False),
        "aggregation": result.get("aggregation", {}),
        "errors": result.get("errors", []),
        "successful_providers": result.get("successful_providers", 0),
        "total_providers": result.get("provider_count", 0),
    }


@router.get("/cache", response_model=Dict[str, Any])
async def get_cache_stats() -> Dict[str, Any]:
    """Get threat cache statistics."""
    from app.threat import get_threat_system
    
    cache = ThreatCache()
    return cache.get_stats()


@router.delete("/cache", response_model=Dict[str, Any])
async def clear_cache(
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Clear threat intelligence cache."""
    from app.threat.cache import ThreatCache
    
    cache = ThreatCache()
    cache.clear()
    
    return {
        "cleared": True,
        "provider_filter": provider,
        "message": "Threat cache cleared successfully",
    }


@router.get("/history", response_model=Dict[str, Any])
async def threat_history(
    skip: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get threat lookup history."""
    from app.threat.engines.aggregator import ReputationAggregator
    
    # This would typically query a database
    # For now, return aggregated history from the aggregator
    aggregator = init_aggregator()
    
    history = aggregator.aggregation_history[-limit:] if aggregator.aggregation_history else []
    
    return {
        "items": history,
        "total": len(aggregator.aggregation_history) if aggregator.aggregation_history else 0,
        "skip": skip,
        "limit": limit,
    }