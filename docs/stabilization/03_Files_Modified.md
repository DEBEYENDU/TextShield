# Files Modified — v2.2.1 Stabilization

## Frontend (JS)
- `static/js/common.js` — expanded to 110 lines: canonical `window.textshield` + aliases `TextShield/App/utils`, exports `escapeHtml, fetchJson/apiRequest, formatTime/formatDate, badge, showToast, showSpinner/hideSpinner, errorHandler, config`, global fallbacks (`window.showToast` etc), idempotent, moved before page scripts.
- `static/js/index.js` — 192→218 lines: defensive `_ts`, `novalidate` handling, frontend logs (request/response/error), validation, `renderResult` guards, `apiRequest` fallback, early return if not on page.
- `static/js/history.js` — defensive `_ts`, `getCanvas` fallback, handle both `history-body`/`history-table-body`, filter/pagination guards, empty state, `showToast`, zero/one/many handling, `fetch` with `limit/offset/direction`.
- `static/js/analytics.js` — 154→~200 lines: `getCanvas` for old/new IDs (`chart-risk` vs `chart-risk-distribution` etc), `setText` guards, fallback to `analytics-stats` container, donut `No data yet`, bar for empty, zero/one/many handling.
- `static/js/kb.js` — 67→~124 lines: defensive, `if (!statusEl && !rebuildBtn) return`, `renderStatus` try/catch, `rebuildBtn` guard, `fetch` with `.catch`, `showToast`, `errorHandler`.
- `static/js/about.js` — defensive `_ts`, guard `body`.
- `app/static/js/knowledge.js` — 176→~200 lines: fixed syntax `) {`, defensive `_ts`, `DOMContentLoaded` try/catch, `fetch(...).catch`, `escapeHtml`, array guards.

## Templates (HTML)
- `app/templates/base.html` — moved `<script src="/static/js/common.js">` **before** `{% block scripts %}` (was after) — ensures order `common → page`.
- `frontend/templates/base.html` — added `common.js` + `{% block scripts %}`.
- `app/templates/index.html` — `form novalidate` + removed `required` from 3 textareas (was blocking hidden required).
- `app/templates/history.html` — added filter selects `f-type/f-class/f-risk`, pagination `prev/next/page-info`, empty `history-empty`, hash column, `tbody id="history-body"` + hidden `history-table-body` compat.
- `app/templates/analytics.html` — no change (JS now handles both IDs).

## Backend (Python)
- `app/core/settings.py` — added `JWT_*` (3), `RAG_MAX_*` (3), `@property APP_ENV` alias + `jwt_*` lowercase aliases, `CONFIG_VERSION 2.2.0`, validation, black/ruff fixes.
- `run.py` — `settings.APP_ENV` → `settings.ENVIRONMENT`.
- `app/main.py` — lifespan: `settings.validate()`, `init_db()`, warm `retriever.store` + `chunk_count` once, warm `classifier.algorithm_name` once, logs, no duplicate init.
- `app/rag/retriever.py` — `status()` no longer loads `provider` (uses `settings.EMBEDDING_PROVIDER` directly, 5s cache, fallback), fast <30ms.
- `app/services/analysis_service.py` — added 7 stage logs (incoming, normalize, ML, indicators, URL, intent, RAG, threat intel, decision, DB save, API response), `full_text` indent fix, `history` row_id log, `exc_info=True`.
- `app/api/routes_analytics.py` — try/except for `from analytics import` fallback to `app.analytics` (fixed `ModuleNotFoundError`).
- `app/api/routes_system.py` — added `/liveness` and `/healthz` (no response_model).
- `app/database/repositories/analytics_repository.py` — not changed (test fixed via `_record` timestamp).
- `app/database/base.py` — already WAL etc (previous RFC).

## Tests
- `tests/test_repositories.py` — `_record` timestamp now `datetime.now(timezone.utc)` (not hardcoded 2026-08-13) → fixes `test_per_day` brittle.
- `tests/test_integration_stabilization.py` — new 6 tests: analyze→history→analytics→KB→refresh→persist, KB <2s, zero/one/many, email/raw, browser pages.

## Config
- `.env.example` — 17→88 lines, grouped, all `Settings` fields, `*_FILE` secrets, comments.

## Docs
- `docs/Configuration.md` (new),  `docs/stabilization/*` 8 reports (this folder).

## Benchmark
- `benchmarks/report.json` timestamp updated (generated_at).
