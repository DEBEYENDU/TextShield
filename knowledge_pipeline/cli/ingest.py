"""CLI: python -m knowledge_pipeline.cli.ingest / python knowledge_pipeline/cli/ingest.py

Examples:
    python ingest.py
    python ingest.py --folder knowledge_base/
    python ingest.py --file fake_kyc.md
    python ingest.py --folder knowledge_base/ --force --verbose
    python ingest.py --dry-run
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TextShield knowledge ingestion (RFC-002)")
    parser.add_argument("--file", type=Path, default=None, help="Single file to ingest")
    parser.add_argument("--folder", type=Path, default=None, help="Folder to ingest (recursive)")
    parser.add_argument("--category", default=None, help="Force category for ingested docs")
    parser.add_argument("--provider", default="hashing", help="Embedding provider")
    parser.add_argument("--force", action="store_true", help="Reprocess even if unchanged")
    parser.add_argument("--dry-run", action="store_true", help="Parse/validate only, no writes")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--strategy", default="paragraph",
                        choices=["fixed", "overlap", "semantic", "heading", "paragraph"])
    parser.add_argument("--batch-size", type=int, default=32)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    pipeline = IngestionPipeline(
        kb_root=args.folder or PROJECT_ROOT / "knowledge_base",
        provider=args.provider, chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap, chunk_strategy=args.strategy,
        batch_size=args.batch_size, dry_run=args.dry_run,
        verbose=args.verbose, force=args.force,
    )
    result = pipeline.run(file=args.file, folder=args.folder, category=args.category)
    print(json.dumps(result, indent=2, default=str))
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
