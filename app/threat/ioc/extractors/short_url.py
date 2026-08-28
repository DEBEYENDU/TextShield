from __future__ import annotations

import re
from typing import List

from ..base import BaseExtractor
from ..models import ExtractedIOC, IOCType
from ..normalizer import Normalizer
from ..validator import Validator


class ShortURLExtractor(BaseExtractor):
    name = "short_url_extractor"
    ioc_type = IOCType.URL_SHORTENER

    SHORTENERS = {
        'bit.ly', 'goo.gl', 't.co', 'ow.ly', 'tinyurl.com', 'is.gd', 'rebrand.ly'
    }
    PATTERN = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)

    def supports(self, text: str) -> bool:
        return bool(self.PATTERN.search(text))

    def extract(self, text: str, source_message: str = "") -> List[ExtractedIOC]:
        results = []
        for m in self.PATTERN.finditer(text):
            raw = m.group(0)
            # check domain
            try:
                from urllib.parse import urlparse
                parsed = urlparse(raw)
                domain = parsed.netloc.lower().split(':')[0]
                if domain in self.SHORTENERS:
                    norm = Normalizer.normalize(raw, IOCType.URL)
                    valid = Validator.validate(norm, IOCType.URL)
                    start, end = m.span()
                    ioc = ExtractedIOC(
                        type=IOCType.URL_SHORTENER,
                        original_value=raw,
                        normalized_value=norm,
                        confidence=0.7 if valid else 0.3,
                        validation_status="valid" if valid else "invalid",
                        start_pos=start,
                        end_pos=end,
                        extractor_name=self.name,
                        context_snippet=text[max(0, start-30):min(len(text), end+30)],
                        source_message=source_message,
                    )
                    results.append(ioc)
            except Exception:
                continue
        return results
