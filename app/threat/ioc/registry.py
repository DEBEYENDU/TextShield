from __future__ import annotations

from typing import Dict, List

from .base import BaseExtractor
from .models import IOCType


class ExtractorRegistry:
    def __init__(self):
        self._extractors: Dict[IOCType, List[BaseExtractor]] = {}

    def register(self, extractor: BaseExtractor) -> None:
        ioc_type = extractor.ioc_type
        self._extractors.setdefault(ioc_type, []).append(extractor)

    def get_extractors(self, ioc_type: IOCType | None = None) -> List[BaseExtractor]:
        if ioc_type:
            return list(self._extractors.get(ioc_type, []))
        extractors = []
        for lst in self._extractors.values():
            extractors.extend(lst)
        return extractors

    def get_all_types(self) -> List[IOCType]:
        return list(self._extractors.keys())


_registry_instance: ExtractorRegistry | None = None


def get_registry() -> ExtractorRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ExtractorRegistry()
    return _registry_instance


def register_extractor(extractor: BaseExtractor) -> None:
    get_registry().register(extractor)
