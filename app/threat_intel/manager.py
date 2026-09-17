"""Threat-intel manager: the full check pipeline.

Message IOCs -> extract -> normalize -> local reputation -> cache ->
privacy gate -> providers (rate-limited) -> aggregate. Every failure
degrades to local/static intelligence; analysis never crashes.
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.threat_intel import aggregator as aggregator_mod
from app.threat_intel.cache import ThreatIntelCache
from app.threat_intel.config import ThreatIntelConfig, config as default_config
from app.threat_intel.exceptions import PrivacyViolationError, RateLimitExceededError
from app.threat_intel.extractor import extract_iocs
from app.threat_intel.models import IOC, ProviderResult
from app.threat_intel.normalizer import normalize_all
from app.threat_intel.privacy import PrivacyPolicy
from app.threat_intel.rate_limit import ProviderRateLimiter
from app.threat_intel.registry import ThreatIntelRegistry
from app.threat_intel.reputation import ReputationStore

logger = get_logger(__name__)


class ThreatIntelManager:
    """Orchestrates extraction through aggregation for one message."""

    def __init__(self, registry: ThreatIntelRegistry | None = None,
                 cfg: ThreatIntelConfig | None = None,
                 cache: ThreatIntelCache | None = None,
                 reputation: ReputationStore | None = None,
                 privacy: PrivacyPolicy | None = None,
                 limiter: ProviderRateLimiter | None = None):
        self.cfg = cfg or default_config
        self.registry = registry
        self.cache = cache or ThreatIntelCache(path=self.cfg.cache_path,
                                               default_ttl=self.cfg.cache_ttl_seconds)
        self.reputation = reputation or ReputationStore()
        self.privacy = privacy or PrivacyPolicy(
            allow_external=self.cfg.allow_external_lookups)
        self.limiter = limiter or ProviderRateLimiter(dict(self.cfg.rate_limits))
        for provider, (per_min, per_day) in self.cfg.rate_limits.items():
            self.limiter.configure(provider, per_min, per_day)

    # ------------------------------------------------------- single IOC
    def check_ioc(self, ioc: IOC,
                  providers: list[str] | None = None) -> dict:
        started = time.perf_counter()
        results: list[ProviderResult] = []
        cached_any = False
        # 1. local reputation always runs (offline-safe)
        try:
            results.append(self.reputation.lookup(ioc.ioc_type, ioc.normalized_value))
        except Exception as exc:
            logger.warning("Reputation lookup failed: %s", exc)
        # 2. configured providers: cache -> privacy -> rate limit -> lookup
        for provider in self._active_providers(providers):
            if ioc.ioc_type not in provider.capabilities:
                continue
            cached = self.cache.get(ioc.ioc_type, ioc.normalized_value, provider.name)
            if cached is not None:
                results.append(cached)
                cached_any = True
                continue
            try:
                shareable = ioc.normalized_value
                if provider.name not in {"mock", "static"}:
                    shareable = self.privacy.shareable_value(ioc)
            except PrivacyViolationError:
                logger.info("Privacy blocked %s for %s", ioc.ioc_type, provider.name)
                continue
            if not self.limiter.allow(provider.name):
                logger.warning("Rate limit hit for %s; using local intel", provider.name)
                continue
            try:
                result = provider.lookup(
                    IOC(original_value=ioc.original_value,
                        normalized_value=shareable, ioc_type=ioc.ioc_type,
                        source_location=ioc.source_location))
                self.limiter.record(provider.name)
                result.ioc = ioc.normalized_value  # keep canonical identity
                self.cache.put(result)
                results.append(result)
            except Exception as exc:
                logger.warning("Provider %s failed on %s: %s",
                               provider.name, ioc.cache_key(), type(exc).__name__)
        hum = aggregator_mod.aggregate(ioc.normalized_value, ioc.ioc_type, results)
        hum["cached"] = cached_any
        hum["duration_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
        logger.info("threat-intel check ioc_type=%s verdict=%s confidence=%.2f "
                    "providers=%d cached=%s duration_ms=%.1f",
                    ioc.ioc_type, hum["aggregated_verdict"], hum["confidence"],
                    len(results), cached_any, hum["duration_ms"])
        return hum

    # ------------------------------------------------------- message
    def check_message(self, text: str,
                      providers: list[str] | None = None) -> dict:
        iocs = normalize_all(extract_iocs(
            text or "", max_per_type=self.cfg.max_iocs_per_message))
        checks = [self.check_ioc(ioc, providers) for ioc in iocs[:self.cfg.max_iocs_per_message * 3]]
        worst = "unknown"
        for rank, level in (("known_malicious", 3), ("suspicious", 2), ("benign", 1)):
            if any(c["aggregated_verdict"] == rank for c in checks):
                worst = rank
                if rank == "known_malicious":
                    break
        # feed reputation for future analyses (malicious only when confirmed)
        for check, ioc in zip(checks, iocs):
            if check["aggregated_verdict"] == "known_malicious":
                try:
                    self.reputation.observe(ioc.ioc_type, ioc.normalized_value, True)
                except Exception:
                    pass
        return {"iocs": [ioc.to_dict() for ioc in iocs],
                "checks": checks, "worst_verdict": worst,
                "n_iocs": len(iocs)}

    # ------------------------------------------------------- helpers
    def _active_providers(self, only: list[str] | None = None):
        if self.registry is None:
            return []
        providers = []
        for name in self.registry.list_providers():
            if only is not None and name not in only:
                continue
            if name not in self.cfg.enabled_providers:
                continue
            provider = self.registry.get_provider(name)
            if provider is not None:
                providers.append(provider)
        return providers


def build_default_manager(cfg: ThreatIntelConfig | None = None) -> ThreatIntelManager:
    """Manager with mock + static providers registered (offline-ready)."""
    from app.threat_intel.providers.mock import MockProvider
    from app.threat_intel.providers.static import StaticProvider
    from app.threat_intel.registry import ThreatIntelRegistry

    registry = ThreatIntelRegistry()
    registry.register(MockProvider())
    registry.register(StaticProvider())
    if (cfg or default_config).gsb_configured:
        from app.threat_intel.providers.google_safe_browsing import (
            GoogleSafeBrowsingAdapter)

        registry.register(GoogleSafeBrowsingAdapter(cfg or default_config))
    if (cfg or default_config).virustotal_configured:
        from app.threat_intel.providers.virustotal import VirusTotalAdapter

        registry.register(VirusTotalAdapter(cfg or default_config))
    return ThreatIntelManager(registry=registry, cfg=cfg)
