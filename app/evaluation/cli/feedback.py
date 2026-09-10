"""CLI: record analyst feedback and inspect the review queue.

Usage:
    python feedback.py --message "..." --verdict false_positive --analyst ana
    python feedback.py --queue
    python feedback.py --stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation.feedback import VERDICTS, FeedbackStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyst feedback workflow")
    parser.add_argument("--message", default="", help="Message under review")
    parser.add_argument("--verdict", default="", choices=[""] + VERDICTS)
    parser.add_argument("--analyst", default="cli")
    parser.add_argument("--comment", default="")
    parser.add_argument("--expected", default="")
    parser.add_argument("--predicted", default="")
    parser.add_argument("--queue", action="store_true", help="Show review queue")
    parser.add_argument("--stats", action="store_true", help="Show feedback stats")
    parser.add_argument("--resolve", default="", help="Resolve feedback id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = FeedbackStore()
    if args.queue:
        print(json.dumps(store.review_queue()[:20], indent=1))
        return 0
    if args.stats:
        print(json.dumps(store.stats(), indent=1))
        return 0
    if args.resolve:
        print(json.dumps({"resolved": store.resolve(args.resolve)}))
        return 0
    if not args.message or not args.verdict:
        print("Provide --message and --verdict, or use --queue/--stats.")
        return 2
    print(json.dumps(store.record(args.message, args.verdict, args.analyst,
                                  args.comment, args.expected,
                                  args.predicted), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
