"""Unicode normalization, artifact removal, whitespace cleanup."""

from __future__ import annotations

import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_BLANK = re.compile(r"\n{3,}")
_HTML_ENTITY = re.compile(r"&(?:#[0-9]+|#x[0-9a-fA-F]+|[a-zA-Z]+);")
_BROKEN_MD = re.compile(r"(\*\*+|--+|__+|~~+|``+)")
_WS = re.compile(r"[ \t\u00a0\u2000-\u200b\u3000]+")


class DocumentCleaner:
    """Remove artifacts, normalize unicode/line-endings, drop empty sections."""

    def __init__(self, min_section_chars: int = 20):
        self.min_section_chars = min_section_chars

    def clean(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = unicodedata.normalize("NFKC", text)
        text = _CONTROL.sub("", text)
        # Drop obvious HTML artifacts that survived parsing
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
        text = re.sub(r"<[^>]{1,200}>", " ", text)
        try:
            import html as _h

            text = _h.unescape(text)
        except Exception:
            pass
        # Collapse broken markdown runs to single spaces
        text = _BROKEN_MD.sub(" ", text)
        # Normalize horizontal whitespace, keep paragraph breaks
        lines = [ _WS.sub(" ", line).strip() for line in text.split("\n") ]
        # Remove empty sections / collapse blank runs
        kept: list[str] = []
        blank_run = 0
        for line in lines:
            if not line:
                blank_run += 1
                if blank_run <= 1:
                    kept.append("")
                continue
            blank_run = 0
            kept.append(line)
        text = "\n".join(kept)
        text = _MULTI_BLANK.sub("\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def clean_sections(self, sections: list[str]) -> list[str]:
        out = []
        for section in sections:
            cleaned = self.clean(section)
            if len(cleaned) >= self.min_section_chars:
                out.append(cleaned)
        return out
