from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import CacheRecord


class InMemoryStorage:
    def __init__(self):
        self._data: Dict[str, CacheRecord] = {}
        self._index_by_ioc: Dict[str, List[str]] = {}

    def put(self, record: CacheRecord) -> None:
        self._data[record.cache_id] = record
        key = f"{record.ioc_type}:{record.normalized_value}"
        self._index_by_ioc.setdefault(key, []).append(record.cache_id)

    def get(self, cache_id: str) -> Optional[CacheRecord]:
        return self._data.get(cache_id)

    def delete(self, cache_id: str) -> bool:
        if cache_id in self._data:
            rec = self._data.pop(cache_id)
            key = f"{rec.ioc_type}:{rec.normalized_value}"
            if key in self._index_by_ioc:
                try:
                    self._index_by_ioc[key].remove(cache_id)
                    if not self._index_by_ioc[key]:
                        del self._index_by_ioc[key]
                except ValueError:
                    pass
            return True
        return False

    def list_all(self) -> List[CacheRecord]:
        return list(self._data.values())

    def find_by_ioc(self, ioc_type: str, normalized_value: str) -> List[CacheRecord]:
        key = f"{ioc_type}:{normalized_value}"
        ids = self._index_by_ioc.get(key, [])
        return [self._data[i] for i in ids if i in self._data]


class PersistentStorage:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, records: List[CacheRecord]) -> None:
        data = [r.to_dict() for r in records]
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self) -> List[CacheRecord]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [CacheRecord.from_dict(d) for d in data]
