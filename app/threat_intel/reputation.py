"""Local reputation: previous findings + internal knowledge base.

Tracks IOC sightings across analyses (malicious/benign counts) so repeat
offenders are recognized without any external call. Unknown IOCs stay
neutral — never auto-trusted.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.logging import get_logger
from app.threat_intel.models import ProviderResult

logger = get_logger(__name__)


class ReputationStore:
    """Persistent local IOC reputation (sightings + outcomes)."""

    def __init__(self, path: str | Path = "data/threat_intel_reputation.json"):
        self.path = Path(path)
        self._entries: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                self._entries = json.loads(self.path.read_text(encoding="utf-8")).get("entries", {})
        except Exception as exc:
            logger.warning("Reputation load failed: %s", exc)
            self._entries = {}

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"version": "1.0",
                                             "entries": self._entries}, indent=1),
                                 encoding="utf-8")
        except Exception as exc:
            logger.warning("Reputation save failed: %s", exc)

    @staticmethod
    def _key(ioc_type: str, normalized: str) -> str:
        return f"{ioc_type}:{normalized.lower()}"

    def observe(self, ioc_type: str, normalized: str, malicious: bool) -> None:
        entry = self._entries.setdefault(self._key(ioc_type, normalized),
                                         {"sightings": 0, "malicious": 0,
                                          "benign": 0, "last_seen": 0.0})
        entry["sightings"] += 1
        entry["malicious" if malicious else "benign"] += 1
        entry["last_seen"] = time.time()
        self._save()

    def lookup(self, ioc_type: str, normalized: str) -> ProviderResult:
        entry = self._entries.get(self._key(ioc_type, normalized))
        if entry is None or entry.get("sightings", 0) == 0:
            return ProviderResult(ioc=normalized, ioc_type=ioc_type,
                                  provider="local", verdict="unknown",
                                  confidence=0.0, sources=["local-reputation"],
                                  raw_summary="never observed")
        total = entry["sightings"]
        ratio = entry.get("malicious", 0) / total
        if ratio >= 0.5 and entry.get("malicious", 0) >= 2:
            verdict, confidence = "known_malicious", round(min(0.95, 0.5 + 0.2 * ratio), 3)
        elif ratio == 0.0 and total >= 3:
            verdict, confidence = "benign", round(min(0.8, 0.4 + 0.1 * total), 3)
        else:
            verdict, confidence = "suspicious", round(ratio, 3)
        return ProviderResult(ioc=normalized, ioc_type=ioc_type,
                              provider="local", verdict=verdict,
                              confidence=confidence,
                              sources=["local-reputation"],
                              raw_summary=f"seen {total}x "
                                          f"({entry.get('malicious', 0)} malicious)")

    def stats(self) -> dict:
        return {"tracked_iocs": len(self._entries)}
