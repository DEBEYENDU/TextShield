# Integration Audit Report — v2.2.1 Stabilization

**Date:** 2026-09-08 | **Branch:** v2.2-dev | **Commit:** 8bf172b

## Scope
Audited entire stack: `app/main.py`, `app/api/*`, `app/services/*`, `app/database/*`, `app/rag/*`, `app/ml/*`, `app/threat/*`, `frontend`/`static/js`/`app/templates`, `tests/*`.

## Findings

### Analyze Workflow
- **Frontend:** `index.html` had `required` on hidden textareas → browser blocked submit when inactive tab empty → no request sent. `index.js` destructured `window.textshield` at parse time before `common.js` loaded → TypeError, no request, no render. Fixed: `novalidate` + remove `required`, defensive namespace, frontend logs, validation, spinner.
- **API:** `POST /api/analyze` correct (`AnalyzeRequest`), but `analysis_service` had minimal logs, no threat intel log, no DB save log, history persisted but not verified. Fixed: added 7 stage logs.
- **ML:** `classifier.predict` ok, but no log for prediction.
- **RAG:** `retriever.retrieve` ok, but not logged.
- **DB:** `db.insert_analysis` commits via `get_connection`, but `_store_history` not logged, and `test_per_day` brittle (hardcoded 2026-08-13 vs now 2026-09-08 → empty).
- **Frontend Rendering:** `renderResult` assumed fields always present, no guard for null `indicators` etc.

### History
- Template `history.html` had `history-table-body` + missing filters/pagination vs `static/js/history.js` expected `history-body`, `f-type`, etc → JS `getElementById` null → early return → empty table. Fixed: add filter selects, pagination, `history-body` + hidden `history-table-body`, empty alert.
- API `GET /api/history` correct, but JS used `limit/offset` while template expected `page`. Fixed: JS now uses `limit/offset/direction/order_by` matching backend `HistoryFilters`.

### Analytics
- `analytics.html` canvases `chart-spam-vs-ham` etc vs `analytics.js` expected `chart-risk` etc → `getContext` null → JS error. Fixed: `getCanvas` fallback for both IDs, handle zero/one/many via `drawDonut` "No data yet" and `drawBars` single bar.

### Knowledge Base
- `retriever.status()` called `self.provider.name` → triggered `create_embedding_provider` → `SentenceTransformer` load → 80s if model download. Also `open_vector_store` not warmed until first request → first `/api/knowledge-base` blocked. Fixed: `status()` now uses `settings.EMBEDDING_PROVIDER` without loading provider, cached 5s; `main.py` lifespan warms `retriever.store` + `store.backend_name` + `chunk_count` once, logs.

### JS Integration
- 5 files used `const { escapeHtml } = window.textshield` → throw if `common.js` after. Fixed: defensive `_ts = window.textshield || ...`, fallback `escapeHtml`, `common.js` now exports all required (`escapeHtml, apiRequest/fetchJson, formatTime/formatDate, badge, showToast, showSpinner/hideSpinner, errorHandler, config`) + global aliases + `base.html` order `common.js` before `{% block scripts %}`.
- `app/static/js/knowledge.js:61` syntax `function displayCategories() const` → missing `{` → parse error.

### FastAPI
- `app/api/routes_analytics.py:7 from analytics import ...` → `ModuleNotFoundError` broke `create_app`. Fixed: try/except fallback to `app.analytics`.
- `app/api/routes_system.py` missing `liveness`/`healthz` for probes (now added).
- `run.py` used `settings.APP_ENV` (renamed to `ENVIRONMENT`) → `AttributeError`. Fixed: `settings.ENVIRONMENT` + `APP_ENV` alias property.

### Database
- `analytics_repository.per_day` brittle date compare, `history_repository` ok, `analytics_repository.totals` ok, `textshield.db` WAL ok.

### Logging
- Missing stage logs for Threat Intel, Decision, DB save, Frontend request/response. Fixed: added 7 logs in `analysis_service` + 3 in `index.js`.

## Files Audited
`app/main.py`, `app/api/*` (7), `app/services/*` (7), `app/database/*` (5), `app/rag/*` (3), `static/js/*` (6), `app/templates/*` (12), `tests/*` (15).
