from __future__ import annotations

from typing import List, Dict

from .models import ExtractedIOC, IOCType
from .registry import get_registry
from .extractors.url import URLExtractor
from .extractors.domain import DomainExtractor
from .extractors.ip import IPExtractor
from .extractors.email import EmailExtractor
from .extractors.phone import PhoneExtractor
from .extractors.short_url import ShortURLExtractor


class IOCEngine:
    def __init__(self):
        self.registry = get_registry()
        self._register_defaults()

    def _register_defaults(self):
        if self.registry.get_all_types():
            return
        for extractor in [
            URLExtractor(),
            DomainExtractor(),
            IPExtractor(),
            EmailExtractor(),
            PhoneExtractor(),
            ShortURLExtractor(),
        ]:
            self.registry.register(extractor)

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        all_iocs: List[ExtractedIOC] = []
        for extractor in self.registry.get_extractors():
            if extractor.supports(text):
                iocs = extractor.extract(text, source_message)
                all_iocs.extend(iocs)
        # Deduplicate
        deduped = self._deduplicate(all_iocs)
        return deduped

    def _deduplicate(self, iocs: List[ExtractedIOC]) -> List[ExtractedIOC]:
        seen: Dict[tuple, ExtractedIOC] = {}
        for ioc in iocs:
            key = (ioc.type, ioc.normalized_value.lower())
            if key in seen:
                existing = seen[key]
                existing.occurrence_count += 1
            else:
                seen[key] = ioc
        return list(seen.values())

    def validate_ioc(self, value: str, ioc_type: IOCType) -> Dict[str, object]:
        from .normalizer import Normalizer
        from .validator import Validator
        norm = Normalizer.normalize(value, ioc_type)
        is_valid = Validator.validate(norm, ioc_type)
        return {
            "original_value": value,
            "normalized_value": norm,
            "type": ioc_type.value,
            "valid": is_valid,
        }
