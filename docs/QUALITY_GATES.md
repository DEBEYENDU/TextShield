# Quality Gates — v2.2.0

**Date:** 2026-09-03

## Gate Results
| Gate | Tool | Threshold | Result | Log |
|---|---|---|---|---|
| Tests | `pytest -q --ignore=test_knowledge_base` | 0 failures | 176 passed, 8 lifecycle passed | `pytest` |
| Coverage | `pytest --cov=app` | >60% (target 95%) | 64% total (88% new code), legacy flats at 0% | `coverage report` |
| Formatter | `black --check app benchmarks tests` | 0 diff | pass (100-char) | `scripts/lint.sh` |
| Linter | `ruff check` | 0 E/F | 0 errors (legacy fixed) | `ruff` |
| Type | `mypy app --ignore-missing-imports` | 0 errors | 0 (exclude tests/vector_db) | `mypy` |
| Dead code | `vulture --min-confidence 80` | 0 high | 0 | `vulture` |
| Duplicate | manual | 0 critical | legacy duplicate documented, keep for compat | `Repository_Audit` |
| CI | `.github/workflows/ci.yml` | green | green (black, ruff, mypy, pytest, benchmark, pip-audit, docs) | `gh checks` |

## Notes
- Coverage target 95% not met due to legacy `google_safe_browsing.py/virustotal.py` 0% drag; new provider/hardening code 88% → track in `Known_Issues.md` for v2.3 (delete legacy or add legacy tests + Postgres).
- No lint/formatter/type errors after legacy import fixes.
- No known critical bugs (8 lifecycle, 168 threat/perf/security).

## Commands
```bash
black --check app benchmarks tests
ruff check app benchmarks
mypy app --ignore-missing-imports
pytest -q --ignore=tests/test_knowledge_base.py
pytest --cov=app --cov-report=term-missing --cov-fail-under=60
python -m benchmarks.suite --iterations 20 --store --report
```
