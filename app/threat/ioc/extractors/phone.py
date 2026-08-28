from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class PhoneExtractor(BaseExtractor):
    name = "phone_extractor"
    ioc_type = IOCType.PHONE

    PHONE_PATTERN = re.compile(r'(?:\+?\d[\d\s\-\(\)]{6,}\d)')

    def supports(self, text: str) -> bool:
        return bool(self.PHONE_PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        seen = set()
        for m in self.PHONE_PATTERN.finditer(text):
            raw = m.group(0)
            norm = Normalizer.normalize(raw, IOCType.PHONE)
            if len(norm.replace('+','')) < 7:
                continue
            if norm in seen:
                continue
            seen.add(norm)
            start, end = m.span()
            valid = Validator.validate(norm, IOCType.PHONE)
            confidence = 0.8 if valid else 0.4
            ioc = ExtractedIOC(
                type=IOCType.PHONE,
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
            results.append(ioc)
        return results
