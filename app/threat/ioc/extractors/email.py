from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class EmailExtractor(BaseExtractor):
    name = "email_extractor"
    ioc_type = IOCType.EMAIL

    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

    def supports(self, text: str) -> bool:
        return bool(self.EMAIL_PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        seen = set()
        for m in self.EMAIL_PATTERN.finditer(text):
            raw = m.group(0)
            norm = Normalizer.normalize(raw, IOCType.EMAIL)
            if norm in seen:
                continue
            seen.add(norm)
            start, end = m.span()
            valid = Validator.validate(norm, IOCType.EMAIL)
            confidence = 0.9 if valid else 0.3
            ioc = ExtractedIOC(
                type=IOCType.EMAIL,
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
