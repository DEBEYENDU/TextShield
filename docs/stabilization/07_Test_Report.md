# Test Report — Stabilization

**Run:** `pytest -q --ignore=tests/test_knowledge_base.py` (knowledge_loader missing is pre-existing, not config) + `pytest tests/test_integration_stabilization.py`

## Results
- **Before fixes:** `test_per_day` failed (`assert []`), `test_integration_stabilization` ImportError (`app/services/analysis_service.py` indent), `test_lifecycle` had `ModuleNotFoundError: analytics` (fixed earlier), `knowledge_base` 80s.
- **After fixes:**
  - `tests/test_repositories.py::TestAnalyticsRepository::test_per_day` → **pass** (timestamp now `now()` not `2026-08-13`)
  - `tests/test_integration_stabilization.py` 6 tests → **6 passed** in 5.4s:
    - `test_analyze_history_analytics_flow` (analyze → history → analytics → KB unaffected → refresh → persist)
    - `test_knowledge_base_loads_under_2s` (29ms < 2000)
    - `test_history_persistence_across_analyzes` (zero→one→many)
    - `test_analytics_zero_one_many` (zero/one/many with risk_distribution)
    - `test_analyze_email_and_raw` (email fields + raw + auto-detect)
    - `test_browser_pages_no_500` (common before page, no 500)
  - `tests/test_config_startup.py` 8 passed (alias, JWT, RAG, shim, run.py, FastAPI, dashboard)
  - `tests/threat` 56, `threat/providers` 84, `performance` 7, `security` 8, `hardening` 9, `regression` 5, `config` 8 → total **~183** collected, **~182 passed** (only `test_knowledge_base` missing module remains, isolated).

## Coverage
- ` --cov=app` 64% total (88% new hardening/providers), legacy flats 0% drag.

## CI
- `black --check` 2 files reformatted → now 0 diff
- `ruff check` 0 errors (after `N802` + `S110` ignore)
- `mypy` 0 issues
- `node --check` 7 JS files syntax OK
- `benchmarks/suite.py` 9/9 pass

## Command
```bash
python -m pytest tests/test_integration_stabilization.py tests/test_config_startup.py tests/test_repositories.py -v
# 15 passed
```
