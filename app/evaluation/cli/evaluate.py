"""CLI: evaluate a dataset or ad-hoc messages.

Usage:
    python evaluate.py --dataset banking
    python evaluate.py --dataset fraud --with-agents --export json
    python -m app.evaluation.cli.evaluate --category phishing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation import reports as reports_mod
from app.evaluation.dataset import DatasetManager
from app.evaluation.evaluator import EvaluationEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate TextShield on a dataset")
    parser.add_argument("--dataset", default=None, help="Collection name (default: all)")
    parser.add_argument("--category", default=None, help="Alias for --dataset")
    parser.add_argument("--version", default=None, help="Run name")
    parser.add_argument("--export", default="markdown",
                        choices=["markdown", "json", "html", "csv", "none"])
    parser.add_argument("--with-agents", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manager = DatasetManager()
    name = args.dataset or args.category
    samples = manager.load_collection(name) if name else manager.load_all()
    run = EvaluationEngine(with_agents=args.with_agents).evaluate(samples)
    summary = reports_mod.summarize_run(run)
    print(json.dumps(summary["metrics"], indent=1))
    if args.export != "none":
        render = {"markdown": reports_mod.to_markdown, "json": reports_mod.to_json,
                  "html": reports_mod.to_html, "csv": reports_mod.to_csv}[args.export]
        ext = {"markdown": ".md", "json": ".json",
               "html": ".html", "csv": ".csv"}[args.export]
        out = Path(f"data/eval/runs/{summary['run_id']}{ext}")
        out.write_text(render(run), encoding="utf-8")
        print(f"exported {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
