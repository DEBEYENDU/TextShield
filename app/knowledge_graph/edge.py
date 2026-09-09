"""Graph edge model."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Edge:
    """A typed, weighted relationship between two nodes."""

    src: str            # source node id
    dst: str            # destination node id
    rel: str            # one of RELATIONSHIPS
    weight: float = 1.0
    evidence: str = ""  # short quoted span justifying the edge

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.src, self.dst, self.rel)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Edge":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})
