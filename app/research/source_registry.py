"""Source registry with reliability metadata."""

from __future__ import annotations
from typing import Dict
from .models import Source
from .enums import SourceType

class SourceRegistry:
    def __init__(self):
        self._sources: Dict[str, Source] = {}

    def register(self, source: Source) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def list_by_type(self, source_type: SourceType) -> list[Source]:
        return [s for s in self._sources.values() if s.source_type == source_type]

    def update_reliability(self, source_id: str, reliability: float, accuracy: float) -> None:
        if source_id in self._sources:
            s = self._sources[source_id]
            s.reliability = reliability
            s.historical_accuracy = accuracy
