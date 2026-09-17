#!/usr/bin/env bash
set -e
echo "== black --check =="
black --check app benchmarks tests || (echo "run: black app benchmarks tests" && exit 1)
echo "== ruff check =="
ruff check app benchmarks || true
echo "== mypy =="
mypy app --ignore-missing-imports || true
echo "== deadcode (vulture) =="
vulture app --min-confidence 80 || true
echo "lint done"
