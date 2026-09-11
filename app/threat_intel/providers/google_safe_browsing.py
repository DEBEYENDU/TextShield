"""Google Safe Browsing adapter: delegates to the existing async provider.

Without TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY the adapter reports
``unavailable`` and never touches the network. With a key it runs the
underlying lookup synchronously (bounded timeout) and normalizes the
ThreatIndicator into the common ProviderResult format.
"""

from __future__ import annotations

import asyncio

from app.threat_intel.config import ThreatIntelConfig, config as default_config
from app.threat_intel.exceptions import ProviderConfigError
from app.threat_intel.models import ProviderResult
from app.threat_intel.provider import ThreatIntelProvider


def _run(coro, timeout: float):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # nested-loop safe fallback: run in a fresh thread loop
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=timeout)
    return asyncio.run(asyncio.wait_for(coro, timeout))


_SEVERITY_MAP = {"malware": "high", "social_engineering": "high",
                 "phishing": "high", "unwanted_software": "medium"}


class GoogleSafeBrowsingAdapter(ThreatIntelProvider):
    """Sync facade over app.threat.providers.google_safe_browsing."""

    name = "google_safe_browsing"
    version = "1.0.0"

    def __init__(self, cfg: ThreatIntelConfig | None = None):
        self.cfg = cfg or default_config
        self._inner = None

    @property
    def capabilities(self) -> list[str]:
        return ["url", "domain"]

    def is_configured(self) -> bool:
        return bool(self.cfg.gsb_configured)

    def _client(self):
        if self._inner is None:
            if not self.is_configured():
                raise ProviderConfigError(
                    "google_safe_browsing: TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY not set")
            from app.threat.providers.google_safe_browsing.provider import (
                GoogleSafeBrowsingProvider)

            self._inner = GoogleSafeBrowsingProvider(
                api_key=self.cfg.google_safe_browsing_key,
                timeout=self.cfg.provider_timeout_seconds)
            self._inner.initialize()
        return self._inner

    def _normalize(self, value: str, ioc_type: str,
                   indicator) -> ProviderResult:
        if indicator is None:
            return ProviderResult(ioc=value, ioc_type=ioc_type,
                                  provider=self.name, verdict="unknown",
                                  confidence=0.0, sources=["google-safe-browsing"],
                                  raw_summary="no match")
        status = str(getattr(indicator, "detection_status", "unknown")).lower()
        verdict = ("known_malicious" if status in {"malicious", "phishing", "malware"}
                   else "suspicious" if status in {"suspicious", "unwanted"}
                   else "benign" if status == "benign" else "unknown")
        confidence = float(getattr(indicator, "confidence", 0.5) or 0.5)
        return ProviderResult(ioc=value, ioc_type=ioc_type, provider=self.name,
                              verdict=verdict, confidence=confidence,
                              categories=[status],
                              sources=["google-safe-browsing"],
                              raw_summary=str(getattr(indicator, "explanation", ""))[:200])

    def _call(self, method: str, value: str, ioc_type: str) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult.unavailable(value, ioc_type, self.name,
                                              reason="unavailable")
        try:
            client = self._client()
            coro = getattr(client, method)(value)
            indicator = _run(coro, self.cfg.provider_timeout_seconds)
            return self._normalize(value, ioc_type, indicator)
        except ProviderConfigError:
            return ProviderResult.unavailable(value, ioc_type, self.name,
                                              reason="unavailable")
        except Exception as exc:
            return ProviderResult(ioc=value, ioc_type=ioc_type,
                                  provider=self.name, verdict="unavailable",
                                  confidence=0.0, provider_status="error",
                                  raw_summary=f"{type(exc).__name__}")

    def lookup_url(self, url: str) -> ProviderResult:
        return self._call("lookup_url", url, "url")

    def lookup_domain(self, domain: str) -> ProviderResult:
        return self._call("lookup_domain", domain, "domain")
