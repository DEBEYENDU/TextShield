"""CLI: render saved reports in any format.

Usage:
    python reports.py --run run-abc123 --export html
    python reports.py --run run-abc123 --export csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation import reports as reports_mod
from app.evaluation.evaluator import EvaluationEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render evaluation reports")
    parser.add_argument("--run", required=True, help="Run id to render")
    parser.add_argument("--export", default="markdown",
                        choices=["markdown", "json", "html", "csv"])
    parser.add_argument("--dataset", default=None, help="Unused (parity)")
    parser.add_argument("--category", default=None, help="Unused (parity)")
    parser.add_argument("--version", default=None, help="Unused (parity)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run = EvaluationEngine().load_run(args.run)
    render = {"markdown": reports_mod.to_markdown, "json": reports_mod.to_json,
              "html": reports_mod.to_html, "csv": reports_mod.to_csv}[args.export]
    print(render(run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
