"""CLI: compare two runs and fail CI on regressions.

Usage:
    python regression.py --old run-aaa --new run-bbb
    python regression.py --old run-aaa --new run-bbb --threshold 0.02
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation.evaluator import EvaluationEngine
from app.evaluation.regression import check_threshold, compare_runs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare evaluation runs (CI gate)")
    parser.add_argument("--old", required=True, help="Baseline run id")
    parser.add_argument("--new", required=True, help="Candidate run id")
    parser.add_argument("--threshold", type=float, default=0.02,
                        help="Max allowed regression rate")
    parser.add_argument("--version", default=None, help="Label (unused, for parity)")
    parser.add_argument("--export", default="none",
                        choices=["markdown", "json", "html", "csv", "none"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = EvaluationEngine()
    comparison = compare_runs(engine.load_run(args.old), engine.load_run(args.new))
    gate = check_threshold(comparison, args.threshold)
    print(json.dumps({**comparison,
                      "improved": comparison["improved"][:10],
                      "regressed": comparison["regressed"][:10],
                      "gate": gate}, indent=1))
    if args.export != "none":
        out = Path(f"data/eval/runs/regression-{args.old}-vs-{args.new}.json")
        out.write_text(json.dumps(comparison, indent=1, default=str), encoding="utf-8")
        print(f"exported {out}")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
