from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class IPExtractor(BaseExtractor):
    name = "ip_extractor"
    ioc_type = IOCType.IP

    IPV4_PATTERN = re.compile(r'\b((?:\d{1,3}\.){3}\d{1,3})\b')
    IPV6_PATTERN = re.compile(r'\b([0-9a-fA-F:]{2,}:[0-9a-fA-F:]+)\b')

    def supports(self, text: str) -> bool:
        return bool(self.IPV4_PATTERN.search(text) or self.IPV6_PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        for m in self.IPV4_PATTERN.finditer(text):
            raw = m.group(1)
            norm = Normalizer.normalize(raw, IOCType.IPV4)
            valid = Validator.validate(norm, IOCType.IPV4)
            start, end = m.span(1)
            ioc_type = IOCType.IPV4
            confidence = 0.95 if valid else 0.2
            results.append(self._make_ioc(raw, norm, ioc_type, valid, confidence, start, end, text, source_message))
        for m in self.IPV6_PATTERN.finditer(text):
            raw = m.group(1)
            norm = Normalizer.normalize(raw, IOCType.IPV6)
            valid = Validator.validate(norm, IOCType.IPV6)
            start, end = m.span(1)
            ioc_type = IOCType.IPV6
            confidence = 0.95 if valid else 0.2
            results.append(self._make_ioc(raw, norm, ioc_type, valid, confidence, start, end, text, source_message))
        return results

    def _make_ioc(self, raw, norm, ioc_type, valid, confidence, start, end, text, source_message):
        return ExtractedIOC(
            type=ioc_type,
            original_value=raw,
            normalized_value=norm,
            confidence=confidence,
            validation_status="valid" if valid else "invalid",
            start_pos=start,
            end_pos=end,
            extractor_name=self.name,
            context_snippet=text[max(0, start-30):min(len(text), end+30)],
            source_message=source_message,
        )
