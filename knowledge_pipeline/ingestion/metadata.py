"""Metadata extraction with sensible defaults and warnings."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SUPPORTED_LANGUAGES = {"en", "unknown"}


@dataclass
class DocumentMetadata:
    doc_id: str
    title: str
    source: str
    category: str
    author: str = "unknown"
    organization: str = "TextShield"
    published: str = ""
    last_updated: str = ""
    language: str = "en"
    tags: list[str] = field(default_factory=list)
    severity: str = "info"
    summary: str = ""
    references: list[str] = field(default_factory=list)


_SEVERITY_WORDS = {
    "critical": "critical",
    "ransomware": "critical",
    "high": "high",
    "malware": "high",
    "phishing": "high",
    "medium": "medium",
    "scam": "medium",
    "fraud": "medium",
    "low": "low",
    "info": "info",
}

_URL = re.compile(r"https?://[^\s)>\]]+")


class MetadataExtractor:
    """Merge parser hints + filesystem info into a complete metadata record."""

    def extract(self, doc_id: str, title: str, text: str, source_path: str,
                category: str, raw: dict | None = None) -> tuple[DocumentMetadata, list[str]]:
        raw = dict(raw or {})
        warnings: list[str] = []
        path = Path(source_path)
        lowered = f"{title}\n{text[:2000]}".lower()

        author = str(raw.get("author") or raw.get("creator") or "unknown")
        if author == "unknown":
            warnings.append(f"{doc_id}: author missing, defaulted to 'unknown'")
        organization = str(raw.get("organization") or raw.get("creator") or "TextShield")
        language = str(raw.get("language") or "en").lower()
        if language not in SUPPORTED_LANGUAGES:
            warnings.append(f"{doc_id}: unsupported language '{language}', kept as-is")

        severity = str(raw.get("severity") or "info").lower()
        if "severity" not in raw:
            for word, level in _SEVERITY_WORDS.items():
                if word in lowered:
                    severity = level
                    break

        tags = raw.get("tags") or raw.get("keywords") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r"[,;]", tags) if t.strip()]
        tags = [str(t).lower() for t in tags][:20]
        if not tags:
            tags = [category.lower()]
            warnings.append(f"{doc_id}: tags missing, defaulted to category")

        summary = str(raw.get("summary") or raw.get("subject") or "")
        if not summary:
            first = next((ln.strip() for ln in text.splitlines() if len(ln.strip()) > 40), "")
            summary = first[:300]
            if not summary:
                warnings.append(f"{doc_id}: summary missing and could not be inferred")

        references = raw.get("references") or []
        if isinstance(references, str):
            references = [references]
        found_urls = _URL.findall(text[:20000])
        for url in found_urls[:10]:
            if url not in references:
                references.append(url)

        now = datetime.now(timezone.utc).isoformat()
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            mtime = now
        published = str(raw.get("published") or raw.get("date") or mtime)

        meta = DocumentMetadata(
            doc_id=doc_id,
            title=title or path.stem,
            source=path.name,
            category=category,
            author=author,
            organization=organization,
            published=published,
            last_updated=mtime,
            language=language,
            tags=tags,
            severity=severity,
            summary=summary,
            references=[str(r) for r in references][:20],
        )
        return meta, warnings

    @staticmethod
    def to_dict(meta: DocumentMetadata) -> dict:
        return asdict(meta)
