"""Threat-intel cache: IOC x provider -> result with TTL expiry.

JSON-file backed, per-provider TTL, hit/miss statistics. Avoids repeated
external requests; stale entries are treated as misses (never served).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.logging import get_logger
from app.threat_intel.models import ProviderResult

logger = get_logger(__name__)


class ThreatIntelCache:
    """Persistent cache keyed by (ioc_type, normalized, provider)."""

    def __init__(self, path: str | Path = "data/threat_intel_cache.json",
                 default_ttl: int = 3600):
        self.path = Path(path)
        self.default_ttl = default_ttl
        self._entries: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0
        self._load()

    # ------------------------------------------------------- persistence
    def _load(self) -> None:
        try:
            if self.path.exists():
                self._entries = json.loads(self.path.read_text(encoding="utf-8")).get("entries", {})
        except Exception as exc:
            logger.warning("Threat-intel cache load failed: %s", exc)
            self._entries = {}

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"version": "1.0",
                                             "entries": self._entries}, indent=1),
                                 encoding="utf-8")
        except Exception as exc:
            logger.warning("Threat-intel cache save failed: %s", exc)

    @staticmethod
    def _key(ioc_type: str, normalized: str, provider: str) -> str:
        return f"{ioc_type}:{normalized.lower()}@{provider}"

    # ------------------------------------------------------- operations
    def get(self, ioc_type: str, normalized: str, provider: str) -> ProviderResult | None:
        entry = self._entries.get(self._key(ioc_type, normalized, provider))
        if entry is None:
            self.misses += 1
            return None
        if entry.get("expires_at", 0) and time.time() > entry["expires_at"]:
            self._entries.pop(self._key(ioc_type, normalized, provider), None)
            self.misses += 1
            return None
        self.hits += 1
        data = dict(entry["result"])
        result = ProviderResult(**{k: v for k, v in data.items() if k != "expired"})
        return result

    def put(self, result: ProviderResult, ttl: int | None = None) -> None:
        now = time.time()
        result.checked_at = now
        result.expires_at = now + (ttl if ttl is not None else self.default_ttl)
        self._entries[self._key(result.ioc_type, result.ioc, result.provider)] = {
            "result": result.to_dict(), "expires_at": result.expires_at}
        self._save()

    def invalidate(self, ioc_type: str, normalized: str, provider: str) -> bool:
        return self._entries.pop(self._key(ioc_type, normalized, provider), None) is not None

    def purge_expired(self) -> int:
        now = time.time()
        expired = [k for k, v in self._entries.items()
                   if v.get("expires_at", 0) and now > v["expires_at"]]
        for key in expired:
            del self._entries[key]
        if expired:
            self._save()
        return len(expired)

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"entries": len(self._entries), "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else 0.0}
