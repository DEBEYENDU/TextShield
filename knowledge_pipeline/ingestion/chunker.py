"""Chunking engine: fixed / overlap / semantic / heading-aware / paragraph-aware."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    index: int
    category: str
    source: str
    strategy: str
    char_start: int
    char_end: int
    metadata: dict = field(default_factory=dict)


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class ChunkManager:
    """Configurable chunker maintaining per-chunk metadata."""

    def __init__(self, chunk_size: int = 700, overlap: int = 100,
                 strategy: str = "paragraph"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    # -- public API -----------------------------------------------------
    def chunk(self, doc_id: str, text: str, metadata: dict,
              strategy: str | None = None) -> list[Chunk]:
        strategy = strategy or self.strategy
        if strategy == "fixed":
            pieces = self._fixed(text)
        elif strategy == "overlap":
            pieces = self._overlap(text)
        elif strategy == "semantic":
            pieces = self._semantic(text)
        elif strategy == "heading":
            pieces = self._heading_aware(text)
        elif strategy == "paragraph":
            pieces = self._paragraph_aware(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        chunks: list[Chunk] = []
        cursor = 0
        for i, piece in enumerate(pieces):
            piece = piece.strip()
            if not piece:
                continue
            start = text.find(piece, cursor)
            if start == -1:
                start = cursor
            end = start + len(piece)
            cursor = max(cursor + 1, start + 1)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}#c{i}",
                    doc_id=doc_id,
                    text=piece,
                    index=i,
                    category=str(metadata.get("category", "general")),
                    source=str(metadata.get("source", "unknown")),
                    strategy=strategy,
                    char_start=start,
                    char_end=end,
                    metadata=dict(metadata),
                )
            )
        return chunks

    # -- strategies ------------------------------------------------------
    def _fixed(self, text: str) -> list[str]:
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def _overlap(self, text: str) -> list[str]:
        size, overlap = self.chunk_size, self.overlap
        if len(text) <= size:
            return [text]
        out, start = [], 0
        while start < len(text):
            end = start + size
            out.append(text[start:end])
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return out

    def _semantic(self, text: str) -> list[str]:
        """Greedy sentence packing up to chunk_size (lightweight semantic)."""
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
        if not sentences:
            return self._overlap(text)
        out, current = [], ""
        for sentence in sentences:
            candidate = (current + " " + sentence).strip()
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    out.append(current)
                while len(sentence) > self.chunk_size:
                    out.append(sentence[:self.chunk_size])
                    sentence = sentence[self.chunk_size:]
                current = sentence
        if current:
            out.append(current)
        return out

    def _heading_aware(self, text: str) -> list[str]:
        parts = _HEADING.split(text)
        # split -> [pre, hashes, title, body, hashes, title, body, ...]
        sections: list[str] = []
        if parts and parts[0].strip():
            sections.append(parts[0].strip())
        i = 1
        while i < len(parts):
            hashes = parts[i] if i < len(parts) else ""
            title = parts[i + 1] if i + 1 < len(parts) else ""
            body = parts[i + 2] if i + 2 < len(parts) else ""
            section = f"{hashes} {title}\n{body}".strip()
            if section:
                sections.append(section)
            i += 3
        if not sections:
            return self._paragraph_aware(text)
        out: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                out.append(section)
            else:
                out.extend(self._overlap(section))
        return out

    def _paragraph_aware(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if not paragraphs:
            return self._overlap(text)
        out, current = [], ""
        for para in paragraphs:
            candidate = (current + "\n\n" + para).strip() if current else para
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    out.append(current)
                if len(para) > self.chunk_size:
                    out.extend(self._overlap(para))
                    current = ""
                else:
                    current = para
        if current:
            out.append(current)
        return out
