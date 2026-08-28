from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class DomainExtractor(BaseExtractor):
    name = "domain_extractor"
    ioc_type = IOCType.DOMAIN

    DOMAIN_PATTERN = re.compile(
        r'''(?i)\b((?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,})\b'''
    )

    def supports(self, text: str) -> bool:
        return bool(self.DOMAIN_PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        seen = set()
        for m in self.DOMAIN_PATTERN.finditer(text):
            raw = m.group(1)
            norm = Normalizer.normalize(raw, IOCType.DOMAIN)
            if norm in seen:
                continue
            seen.add(norm)
            start, end = m.span(1)
            valid = Validator.validate(norm, IOCType.DOMAIN)
            confidence = 0.85 if valid else 0.4
            ioc = ExtractedIOC(
                type=IOCType.DOMAIN,
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
