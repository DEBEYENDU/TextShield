"""Build (or rebuild) the RAG knowledge base vector store.

Reads documents from ``knowledge_base/``, chunks them, embeds the chunks
and stores everything in the local vector database.

The vector database persists - it is only rebuilt when this script runs
(or when triggered from the dashboard).

Usage:
    python scripts/build_knowledge_base.py [--kb DIR] [--out DIR] [--provider NAME]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings import create_embedding_provider
from app.rag.vector_store import open_vector_store

logger = get_logger(__name__)

KB_DIR = PROJECT_ROOT / "knowledge_base"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

_MARKDOWN_NOISE = re.compile(r"[#*`>_~\-]{1,3}")


def read_documents(kb_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, cleaned_text) pairs for every .md/.txt file in the KB."""
    documents = []
    for path in sorted(kb_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            text = _MARKDOWN_NOISE.sub(" ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) >= 60:
                documents.append((path, text))
    return documents


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks on paragraph/sentence boundaries."""
    if len(text) <= size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        if end < len(text):
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
                text.rfind("\n", start, end),
            )
            if boundary > start + (size // 3):
                end = boundary + 1
        chunks.append(text[start:end].strip())
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def build(kb_dir: Path = KB_DIR, out_dir: Path | None = None, provider_name: str | None = None) -> dict:
    logger = get_logger(__name__)
    kb_dir = Path(kb_dir)
    out_dir = Path(out_dir or settings.VECTOR_DB_PATH)
    provider = create_embedding_provider(provider_name)

    documents = read_documents(kb_dir)
    if not documents:
        raise FileNotFoundError(f"No knowledge-base documents found in {kb_dir}")

    chunk_ids, chunk_texts, chunk_metas = [], [], []
    categories = sorted({text_path.parent.name for text_path, _ in documents})
    index = 0
    for text_path, text in documents:
        category = text_path.parent.name
        for chunk in chunk_text(text):
            chunk_ids.append(f"{category}:{text_path.stem}:{index}")
            chunk_texts.append(chunk)
            chunk_metas.append(
                {
                    "source": text_path.name,
                    "category": category,
                    "is_example": int(category == "examples"),
                }
            )
            index += 1

    print(f"[+] documents : {len(documents)}")
    print(f"[+] categories: {', '.join(categories)}")
    print(f"[+] chunks    : {len(chunk_texts)}")
    print(f"[+] embedding : {provider.name} (dim {provider.dimension})")
    print(f"[+] backend   : storing in {out_dir}")

    store = open_vector_store(out_dir)
    store.delete_all()
    embeddings = provider.embed(chunk_texts)
    store.add(chunk_ids, embeddings, chunk_texts, chunk_metas)

    info = {
        "backend": store.backend_name,
        "embedding_provider": provider.name,
        "embedding_model": getattr(provider, "_model_name", None),
        "dimension": int(provider.dimension),
        "chunk_count": len(chunk_texts),
        "document_count": len(documents),
        "categories": categories,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    store.save_structure(info)
    print(f"[+] built knowledge base: {len(chunk_texts)} chunks, "
          f"{store.backend_name} backend")

    # quick self-check: embed & query the store to confirm it is searchable
    probe = provider.embed_one("your bank account will be blocked, click here to verify")
    hits = store.query(probe, top_k=2)
    print(f"[+] self-check: top-2 hits -> {[h['metadata'].get('category') for h in hits]}")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the TextShield knowledge base")
    parser.add_argument("--kb", type=Path, default=KB_DIR)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    build(args.kb, args.out, args.provider)


if __name__ == "__main__":
    main()