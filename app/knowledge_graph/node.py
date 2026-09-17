"""Graph node model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class Node:
    """A single entity in the context graph."""

    id: str                      # "TYPE:normalized" — globally unique
    type: str                    # one of ENTITY_TYPES
    label: str                   # display label (first-seen surface form)
    normalized: str              # canonical key from the entity linker
    confidence: float = 0.7
    first_seen: str = field(default_factory=_now)
    last_seen: str = field(default_factory=_now)
    sightings: int = 1           # messages this entity appeared in
    threat_hits: int = 0         # appearances in threat-leaning messages
    legit_hits: int = 0          # appearances in trust-leaning messages
    attrs: dict = field(default_factory=dict)

    def touch(self, *, threat_leaning: bool = False, legit_leaning: bool = False,
              confidence: float | None = None) -> None:
        self.sightings += 1
        self.last_seen = _now()
        if threat_leaning:
            self.threat_hits += 1
        if legit_leaning:
            self.legit_hits += 1
        if confidence is not None:
            self.confidence = round(max(self.confidence, confidence), 3)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
