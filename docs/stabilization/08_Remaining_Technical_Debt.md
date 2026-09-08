# Remaining Technical Debt (if any)

## Open (non-blocking for v2.2.1)
- **Legacy flat providers:** `app/threat/providers/google_safe_browsing.py` + `virustotal.py` duplicate package providers (marked deprecated header) — keep for compat, delete in v2.3 to reach 95% coverage.
- **RAG duplication:** `RagConfig` still defines `RAG_TOP_K=5` vs `Settings.RAG_TOP_K=4` — canonical is `Settings`; recommend removing `RagConfig` defaults and importing directly.
- **SQLite WAL single-instance:** For HA, migrate to Postgres + `asyncpg` pooling (noted in `docs/Configuration.md` Production Mode).
- **Frontend:** `analytics.html` still has 7 canvases but `analytics.js` now handles both old/new; consider unifying to single set and removing fallback `getCanvas` in v2.3.
- **Lighthouse:** 92 → 95 target, PWA/service-worker missing.
- **Mutation tests:** Skipped.

## Closed in Stabilization
- KB 80s → 29ms, history empty → renders, analytics JS errors → handled zero/one/many, analyze `required` → `novalidate`, `window.textshield` destructuring → defensive, `knowledge.js` syntax error, `per_day` brittle date, missing JWT/RAG config, `run.py` `APP_ENV`, `routes_analytics` import, logging gaps.

## Risk
None blocking staging. All acceptance criteria now pass; track above in `Technical_Debt_Report.md` for v2.3.
