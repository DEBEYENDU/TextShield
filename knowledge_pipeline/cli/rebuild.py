"""CLI: full rebuild of the vector database from the knowledge base.

Examples:
    python rebuild.py
    python rebuild.py --force
    python rebuild.py --folder knowledge_base/ --provider hashing
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from knowledge_pipeline.pipeline import IngestionPipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild the TextShield knowledge base")
    parser.add_argument("--folder", type=Path, default=None)
    parser.add_argument("--provider", default="hashing")
    parser.add_argument("--force", action="store_true", default=True,
                        help="Rebuild always clears the store (default on)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    pipeline = IngestionPipeline(
        kb_root=args.folder or PROJECT_ROOT / "knowledge_base",
        provider=args.provider, force=True, verbose=args.verbose,
    )
    result = pipeline.rebuild_all()
    info = pipeline.build_info()
    # Persist structure.json-compatible info for the RAG retriever status.
    try:
        pipeline.indexer.store.save_structure(info)
    except Exception:
        pass
    print(json.dumps({"result": result, "build": info}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
