"""CLI: run benchmark collections with one command.

Usage:
    python benchmark.py
    python benchmark.py --dataset banking --export markdown
    python benchmark.py --dataset fraud --dataset bec --with-agents
    python -m app.evaluation.cli.benchmark --dataset phishing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation import benchmark as benchmark_mod
from app.evaluation import reports as reports_mod


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TextShield benchmark collections")
    parser.add_argument("--dataset", action="append", default=None,
                        help="Collection to run (repeatable; default: all)")
    parser.add_argument("--category", default=None,
                        help="Alias for --dataset (single collection)")
    parser.add_argument("--version", default=None, help="Run name prefix")
    parser.add_argument("--export", default="markdown",
                        choices=["markdown", "json", "html", "csv", "none"])
    parser.add_argument("--with-agents", action="store_true",
                        help="Include multi-agent opinions per sample (slower)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    collections = args.dataset or ([args.category] if args.category else None)
    results = benchmark_mod.run_benchmark(collections, with_agents=args.with_agents)
    failed = 0
    for name, payload in results.items():
        if "error" in payload:
            print(f"[FAIL] {name}: {payload['error']}")
            failed += 1
            continue
        summary = payload["summary"]
        m = summary["metrics"]
        print(f"[{name}] acc={m['accuracy']} f1={m['f1']} "
              f"fpr={m['false_positive_rate']} fnr={m['false_negative_rate']} "
              f"n={summary['n_samples']} run={summary['run_id']}")
        if args.export != "none":
            render = {"markdown": reports_mod.to_markdown,
                      "json": reports_mod.to_json,
                      "html": reports_mod.to_html,
                      "csv": reports_mod.to_csv}[args.export]
            ext = {"markdown": ".md", "json": ".json",
                   "html": ".html", "csv": ".csv"}[args.export]
            out = Path(f"data/eval/runs/{summary['run_id']}{ext}")
            out.write_text(render(payload["run"]), encoding="utf-8")
            print(f"  -> exported {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
