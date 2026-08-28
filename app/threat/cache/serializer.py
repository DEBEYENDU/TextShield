from __future__ import annotations

import json
from typing import List

from .models import CacheRecord


class CacheSerializer:
    @staticmethod
    def to_json(records: List[CacheRecord]) -> str:
        return json.dumps([r.to_dict() for r in records])

    @staticmethod
    def from_json(data: str) -> List[CacheRecord]:
        items = json.loads(data)
        return [CacheRecord.from_dict(d) for d in items]

    @staticmethod
    def export(records: List[CacheRecord], path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(CacheSerializer.to_json(records))

    @staticmethod
    def import_data(path: str) -> List[CacheRecord]:
        with open(path, "r", encoding="utf-8") as f:
            return CacheSerializer.from_json(f.read())
