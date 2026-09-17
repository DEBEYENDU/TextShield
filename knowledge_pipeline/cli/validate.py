"""CLI: validate documents without indexing.

Examples:
    python validate.py
    python validate.py --folder knowledge_base/
    python validate.py --file fake_kyc.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from knowledge_pipeline.ingestion.cleaner import DocumentCleaner
from knowledge_pipeline.ingestion.loader import DocumentLoader
from knowledge_pipeline.ingestion.metadata import MetadataExtractor
from knowledge_pipeline.ingestion.parser import parse_file
from knowledge_pipeline.ingestion.validator import DocumentValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TextShield knowledge documents")
    parser.add_argument("--file", type=Path, default=None)
    parser.add_argument("--folder", type=Path, default=None)
    parser.add_argument("--category", default=None)
    args = parser.parse_args(argv)

    target = args.file or args.folder or (PROJECT_ROOT / "knowledge_base")
    loader = DocumentLoader(target, category=args.category)
    discovered = loader.discover()
    cleaner = DocumentCleaner()
    extractor = MetadataExtractor()
    validator = DocumentValidator()
    reports = []
    for item in discovered:
        try:
            doc = parse_file(item.path, category=item.category)
            cleaned = cleaner.clean(doc.text)
            meta, warnings = extractor.extract(doc.doc_id, doc.title, cleaned,
                                               str(item.path), item.category, doc.raw_metadata)
            meta_dict = MetadataExtractor.to_dict(meta)
            meta_dict["_warnings"] = warnings
            report = validator.validate(doc.doc_id, meta.title, cleaned, meta_dict)
            reports.append(report.to_dict())
            status = "VALID" if report.valid else "INVALID"
            print(f"[{status}] {doc.doc_id}: "
                  f"{len(report.errors)} errors, {len(report.warnings)} warnings")
        except Exception as exc:
            reports.append({"doc_id": str(item.path), "valid": False,
                            "errors": [{"message": str(exc)}], "warnings": []})
            print(f"[ERROR] {item.path}: {exc}")
    valid = sum(1 for r in reports if r["valid"])
    print(json.dumps({"total": len(reports), "valid": valid,
                      "invalid": len(reports) - valid}, indent=2))
    return 0 if valid == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
