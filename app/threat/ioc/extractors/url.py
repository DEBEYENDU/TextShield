from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class URLExtractor(BaseExtractor):
    name = "url_extractor"
    ioc_type = IOCType.URL

    URL_PATTERN = re.compile(
        r'''(?i)\b((?:https?://|ftp://|www\.)[^\s<>"'`]+)'''
    )

    def supports(self, text: str) -> bool:
        return bool(self.URL_PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        for m in self.URL_PATTERN.finditer(text):
            raw = m.group(1)
            start, end = m.span(1)
            norm = Normalizer.normalize(raw, IOCType.URL)
            valid = Validator.validate(norm, IOCType.URL)
            confidence = 0.9 if valid else 0.3
            ioc = ExtractedIOC(
                type=IOCType.URL,
                original_value=raw,
                normalized_value=norm,
                confidence=confidence,
                validation_status="valid" if valid else "invalid",
                start_pos=start,
                end_pos=end,
                extractor_name=self.name,
                context_snippet=text[max(0, start-30):min(len(text), end+30)],
                source_message=source_message,
                metadata={"raw": raw}
            )
            results.append(ioc)
        return results
