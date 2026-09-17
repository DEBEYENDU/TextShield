"""VirusTotal adapter: delegates to the existing async provider.

Without TEXTSHIELD_VIRUSTOTAL_API_KEY the adapter reports ``unavailable``
and never touches the network. With a key it runs the underlying lookup
synchronously (bounded timeout) and normalizes into ProviderResult.
"""

from __future__ import annotations

from app.threat_intel.config import ThreatIntelConfig, config as default_config
from app.threat_intel.exceptions import ProviderConfigError
from app.threat_intel.models import ProviderResult
from app.threat_intel.provider import ThreatIntelProvider
from app.threat_intel.providers.google_safe_browsing import _run


class VirusTotalAdapter(ThreatIntelProvider):
    """Sync facade over app.threat.providers.virustotal."""

    name = "virustotal"
    version = "1.0.0"

    def __init__(self, cfg: ThreatIntelConfig | None = None):
        self.cfg = cfg or default_config
        self._inner = None

    @property
    def capabilities(self) -> list[str]:
        return ["url", "domain", "ipv4", "ipv6", "md5", "sha1", "sha256"]

    def is_configured(self) -> bool:
        return bool(self.cfg.virustotal_configured)

    def _client(self):
        if self._inner is None:
            if not self.is_configured():
                raise ProviderConfigError(
                    "virustotal: TEXTSHIELD_VIRUSTOTAL_API_KEY not set")
            from app.threat.providers.virustotal.provider import VirusTotalProvider

            self._inner = VirusTotalProvider(
                api_key=self.cfg.virustotal_key,
                timeout=self.cfg.provider_timeout_seconds)
            self._inner.initialize()
        return self._inner

    def _normalize(self, value: str, ioc_type: str,
                   indicator) -> ProviderResult:
        if indicator is None:
            return ProviderResult(ioc=value, ioc_type=ioc_type,
                                  provider=self.name, verdict="unknown",
                                  confidence=0.0, sources=["virustotal"],
                                  raw_summary="no match")
        status = str(getattr(indicator, "detection_status", "unknown")).lower()
        verdict = ("known_malicious" if status in {"malicious", "phishing", "malware"}
                   else "suspicious" if status == "suspicious"
                   else "benign" if status == "benign" else "unknown")
        confidence = float(getattr(indicator, "confidence", 0.5) or 0.5)
        return ProviderResult(ioc=value, ioc_type=ioc_type, provider=self.name,
                              verdict=verdict, confidence=confidence,
                              categories=[status], sources=["virustotal"],
                              raw_summary=str(getattr(indicator, "explanation", ""))[:200])

    def _call(self, method: str, value: str, ioc_type: str) -> ProviderResult:
        if not self.is_configured():
            return ProviderResult.unavailable(value, ioc_type, self.name,
                                              reason="unavailable")
        try:
            client = self._client()
            indicator = _run(getattr(client, method)(value),
                             self.cfg.provider_timeout_seconds)
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

    def lookup_ip(self, ip: str) -> ProviderResult:
        return self._call("lookup_ip", ip, "ipv4")

    def lookup_hash(self, hash_value: str) -> ProviderResult:
        kind = {32: "md5", 40: "sha1"}.get(len(hash_value), "sha256")
        return self._call("lookup_hash", hash_value, kind)
