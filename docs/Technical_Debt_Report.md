# TextShield V2.0 — Technical Debt Report

**Phase:** 3 — Repository Audit & Refactoring Plan
**Scope:** Steps 5 (Technical Debt), 8 (Dependency Review), 10 (API Review), 11 (Database Review), 12 (Frontend Review), 13 (Testing Review), 14 (Documentation Review)

---

## 5. Technical Debt

Severity: **HIGH** (must fix), **MED** (should fix), **LOW** (nice to fix).

### 5.1 Code smells

| # | Severity | Smell | Location | Recommendation |
|---|---|---|---|---|
| T-01 | MED | Large orchestrator function (229 lines) with many sequential stages | `analysis_service.py` | Split into step functions (Migration Phase 2) |
| T-02 | MED | Deeply nested conditional input-handling block | `analysis_service.py` (~90–125) | Extract input-parsing to `_prepare_inputs()` |
| T-03 | LOW | Layout engine mixed with content logic in templates | `index.html`, `history.html` | Keep; introduce macros for repeated patterns |
| T-04 | LOW | Repeated JS escaping/fetch boilerplate across 5 scripts | `static/js/*.js` | Extract `common.js` (DRY) |
| T-05 | LOW | Magic strings for levels/labels repeated across modules | `risk_engine.py`, `analysis_service.py`, `generator.py`, JS | Centralize in `app/core/constants.py` + JS constants object |
| T-06 | MED | `description` duplicated in `intent.py` (pattern dicts + `_DESCRIPTIONS`) | `app/ml/intent.py` | Derive from a single dict |
| T-07 | LOW | `extract_urls` called twice in indicator checks | `app/ml/indicators.py` | Compute once per call |
| T-08 | LOW | Route handlers rely on exceptions rather than explicit service return types | `routes_analysis.py` | Acceptable; document mapping (keep) |

### 5.2 Duplicate logic

| # | Severity | Duplication | Location | Recommendation |
|---|---|---|---|---|
| D-01 | MED | Risk-level strings (`LOW|MEDIUM|HIGH|CRITICAL|UNCERTAIN`) repeated in schema, engine, generator, JS, templates | multiple | Central constants (T-05) |
| D-02 | LOW | History record assembly duplicated conceptually between `models.py` and `_store_history` | `database/`, `analysis_service.py` | Move assembly into `database.py` |
| D-03 | LOW | Evidence-truncation limits (420 chars) hardcoded in JS | `index.js`, `history.js` | Constants object |

### 5.3 Large functions

| # | Location | Current size | Action |
|---|---|---|---|
| T-01 | `analysis_service.analyze()` | 229-line module / ~140-line function | Split into steps |
| T-02 | `database.aggregate_stats()` | ~40 lines of queries | Fine; annotate or extract query builders |

### 5.4 Unused files / dead code / orphaned artifacts

| # | Severity | Item | Status | Action |
|---|---|---|---|---|
| U-01 | LOW | `data/processed/*.csv` + `dataset_info.json` | Runtime artifacts, gitignored | Keep local; document regeneration via `prepare_dataset.py` |
| U-02 | LOW | `.pytest_cache/` | Not in `.gitignore` | Add to `.gitignore` |
| U-03 | LOW | `textshield.db` (≈41 rows) | Runtime, gitignored | Keep; add startup migration guard (Phase 4) |
| U-04 | LOW | `logs/textshield.log` | Runtime, gitignored | Keep; rotate in Phase 9 |
| U-05 | INFO | No orphaned source modules | — | None |

### 5.5 Security issues

| # | Severity | Issue | Status | Action |
|---|---|---|---|---|
| S-01 | HIGH | Not applicable — no findings | Audited | No secrets in code; `.env` ignored; output escaping in JS; static-only URL analysis; localhost bind default |
| S-02 | MED | Prompt-injection surface exists when LLM enabled | Mitigated by design (verdict path never consumes LLM output) | Keep; add adversarial test payloads (Phase 7) |
| S-03 | LOW | No rate limiting on public-facing endpoints if exposed beyond localhost | Default bind 127.0.0.1 | Document; optional middleware when LAN exposure configured (Phase 9) |

### 5.6 Performance issues

| # | Severity | Issue | Status | Action |
|---|---|---|---|---|
| P-01 | MED | RAG status disk read per analyze | Fixed with 5 s TTL cache (Phase 2 work) | Verify under load |
| P-02 | LOW | `aggregate_stats()` recomputed on every `/api/stats` call | Correct at scale | Optional 30 s cache (Phase 8) |
| P-03 | LOW | Model loaded once (good); embeddings lazy (good) | OK | Performance baseline script (Phase 7) |

### 5.7 Poor folder organization

| # | Severity | Issue | Recommendation |
|---|---|---|---|
| F-01 | LOW | All schemas in one file | Split (Migration Phase 2) |
| F-02 | LOW | Health router hosts KB endpoints | Split (Migration Phase 2) |
| F-03 | LOW | No lint/type config | Add `pyproject.toml` + ruff (Phase 1) |

### 5.8 Configuration issues

| # | Severity | Issue | Recommendation |
|---|---|---|---|
| C-01 | LOW | Risk weights/thresholds are constants, not env-tunable | Documented design choice (determinism); keep |
| C-02 | LOW | `.env.example` lacks embedding note about PyTorch footprint | Add comment (already noted in requirements) |
| C-03 | MED | No validation warning for inconsistent provider settings (e.g., chromadb missing) | Add startup config health report (Phase 9) |

### 5.9 Hardcoded values

| # | Severity | Value | Location | Action |
|---|---|---|---|---|
| H-01 | LOW | Evidence truncation 420 chars | JS | Constants object |
| H-02 | LOW | Indicator evidence 40 chars, URL truncations 40/60 | `indicators.py`, JS | Keep; document |
| H-03 | LOW | `HISTORY_PREVIEW_LENGTH=120` default | config | OK (env-driven) |

### 5.10 Missing documentation / tests / coverage

See Steps 13 and 14 below.

---

## 8. Dependency Review

### 8.1 Runtime dependencies (`requirements.txt`)

| Dependency | Verdict | Justification |
|---|---|---|
| `fastapi>=0.110,<1.0` | **Required** | API framework |
| `uvicorn[standard]>=0.29` | **Required** | ASGI server |
| `pydantic>=2.6` | **Required** | Validation/contracts |
| `jinja2>=3.1` | **Required** | Templates |
| `python-multipart>=0.0.9` | **Required** (minimal) | Form parsing; could be optional if UI is JSON-only — keep for safety |
| `python-dotenv>=1.0` | **Required** | Config loading |
| `joblib>=1.3` | **Required** | Model persistence |
| `numpy>=1.26` | **Required** | Embeddings/features |
| `scikit-learn>=1.4` | **Required** | ML pipeline |
| `requests>=2.31` | **Required** | LLM HTTP calls |
| `pandas>=2.2` | **Required for scripts**, optional at runtime | Used by `prepare_dataset.py`/`train_model.py` only |
| `chromadb>=0.4.24` | **Optional (primary backend)** | Falls back to numpy store |
| `sentence-transformers>=2.7` | **Optional (primary embedder)** | Pulls PyTorch; hashing fallback exists |
| `aiofiles>=23.2` | **Required** | Static file serving on Python 3.13+ |
| `pytest>=8.0` | **Dev** | Test runner |
| `httpx>=0.27` | **Dev** | TestClient transport |

### 8.2 Findings and recommendations

| # | Finding | Recommendation |
|---|---|---|
| R-01 | `httpx` pinned `>=0.27` causes Starlette deprecation warning on Python 3.14 (httpx2) | Accept for now; track upstream; document in `pytest.ini` comment |
| R-02 | `chromadb` + `sentence-transformers` are optional in practice (fallbacks exist) | Split into `requirements-core.txt` / `requirements-rag.txt` for lighter installs |
| R-03 | `pandas` only needed by scripts | Move to `requirements-dev.txt` or a `requirements-scripts.txt` |
| R-04 | No lint/format/type tooling | Add `ruff` + optional `mypy` to dev requirements |
| R-05 | No coverage tooling | Add `pytest-cov` to dev requirements |
| R-06 | `requests` is the only HTTP client in runtime | Fine; consider `httpx` if async needed later |
| R-07 | Deprecated versions: none observed | Pin minor versions in `requirements.lock` for reproducibility |

---

## 10. API Review

### 10.1 Endpoint inventory

| Endpoint | Method | Purpose | Verdict |
|---|---|---|---|
| `/api/analyze` | POST | Full analysis | **REUSE** (V2 fields already added) |
| `/api/history` | GET | List with filters/pagination | **REUSE** + extend filter by `intent`, `risk_level` (existing) |
| `/api/history/{id}` | DELETE | Single delete | **REUSE** |
| `/api/history` | DELETE | Clear all | **REUSE** |
| `/api/stats` | GET | Aggregates | **REUSE** (+ optional intent distribution when column exists) |
| `/api/model-info` | GET | Model metadata | **REUSE** (+ calibration details via Model Manager) |
| `/api/health` | GET | Component health | **REUSE** |
| `/api/knowledge-base` | GET | KB status/categories | **REUSE** |
| `/api/knowledge-base/rebuild` | POST | Rebuild index | **REUSE** |
| `/` `/history` `/analytics` `/knowledge-base` `/about` | GET | Pages | **REUSE** |

### 10.2 Required changes

| Endpoint | Change | Phase |
|---|---|---|
| `GET /api/history` | Optional `intent` filter parameter | 4 |
| `GET /api/stats` | Optional `intent_distribution` key | 4 |
| All | Document V2 fields (`intent`, `risk_score`, CRITICAL/UNCERTAIN) in `docs/api.md` | 5 |

### 10.3 New endpoints (target)

| Endpoint | Method | Purpose | Priority |
|---|---|---|---|
| `/api/config` | GET | Effective configuration (read-only) for About/settings | Future |
| `/api/history/export` | GET | CSV/JSON export for researchers | Future |
| `/api/knowledge-base/{category}/{document}` | GET | Individual document content | Future |

### 10.4 Endpoints to deprecate

None. All existing endpoints remain valid; no versioning needed at this scale.

---

## 11. Database Review

### 11.1 Current state

- Single table `analyses` + indexes on `timestamp`, `classification`.
- All access through `database.py` (parameterized, column allow-list, thread-safe).

### 11.2 Verdicts

| Item | Verdict | Notes |
|---|---|---|
| `analyses` table | **REUSE** | Add `intent TEXT` column (nullable, backfill) |
| `idx_analyses_timestamp` | REUSE | |
| `idx_analyses_classification` | REUSE | Consider covering index with `risk_level` |
| `kb_metadata` table | **NEW** (design target) | Mirror `structure.json`; feed `rag_status` |
| `app_settings` table | **NEW** (future) | Settings screen (Phase 9+) |
| `system_logs` table | **NEW** (future) | Audit trail (Phase 9) |

### 11.3 Schema improvements

| # | Improvement | Detail |
|---|---|---|
| DB-01 | Add `intent` column | `ALTER TABLE ... ADD COLUMN intent TEXT` guarded by `PRAGMA table_info` check (idempotent migration) |
| DB-02 | Add index on `risk_level` | Analytics queries group by it |
| DB-03 | Timestamps as ISO-8601 UTC text | Already consistent; keep (no TZ math) |
| DB-04 | Backfilled rows default intent `NULL` | Display "n/a" in UI filters |
| DB-05 | Add `model_version` column (optional) | Tracks verdict provenance per row (future) |

### 11.4 Normalization opportunities

- Risk levels could be a lookup table — **not warranted** (5 fixed values, no joins); keep as TEXT with a CHECK-like validation in code.
- `kb_metadata` is a snapshot, not relational; keep 1:1 with the index (documented in SDD §10.3).

---

## 12. Frontend Review

### 12.1 UI/UX

| Area | Assessment | Action |
|---|---|---|
| Analyze flow | Clear 3-tab intake; result hero + evidence sections | Keep; add loading skeletons |
| History | Table + filters + pagination | Keep; add intent column/filter after DB-01 |
| Analytics | Local canvas charts (no CDN) | Keep; add intent distribution chart |
| KB page | Category browsing + rebuild | Keep; add per-document detail (future) |
| About | Health/model/privacy content | Keep; add config readout (future) |

### 12.2 Responsiveness

| Assessment | Action |
|---|---|
| Single stylesheet with fluid grid; works on mobile browsers | Add explicit breakpoint audit (≤768 px) in Phase 6 |

### 12.3 Accessibility

| Issue | Action (Phase 6) |
|---|---|
| Verdicts communicated partly by color | Add text badges already present; ensure aria-labels on chips |
| No visible focus states documented | Add `:focus-visible` styles |
| Tabs lack full keyboard semantics | Add `aria-selected`, arrow-key navigation |
| Contrast of muted text on dark theme | Audit against WCAG AA; adjust |

### 12.4 Navigation & visual consistency

| Area | Assessment | Action |
|---|---|---|
| Shared `base.html` nav | Consistent | Add active-page highlighting |
| Badges/chips/cards reused across pages | Consistent | Centralize renderers in `common.js` |
| Theme variables in `style.css` | Consistent | Keep; document color tokens |

### 12.5 Reusable components (inventory)

| Component | Used in | Action |
|---|---|---|
| `escapeHtml` | index/history/analytics/kb/about | Extract to `common.js` |
| Verdict/risk badges | index/history | Extract |
| Card + list markup | all pages | Jinja2 macro |
| Chart renderer | analytics | Keep single |
| Result/error alert toast | index | Extract |

---

## 13. Testing Review

### 13.1 Existing coverage (93 tests passing)

| Module | Tests | Coverage level |
|---|---|---|
| preprocessing | 9 | Good |
| classifier | 6 | Good |
| indicators | 9 | Good |
| intent | 10 | Good |
| url_analyzer | 8 | Good |
| risk | 15 | Good |
| rag (retriever/store) | 10 | Partial (no vector_store unit tests) |
| api | 18 | Good (via TestClient) |

### 13.2 Gaps

| # | Missing test | Why | Priority |
|---|---|---|---|
| G-01 | `generator` (template determinism, recommendation matrix, LLM fallback with mocked client) | Core explanation surface untested | HIGH |
| G-02 | `database` (insert/query/delete/clear/stats, column allow-list, migration guard) | Persistence untested directly | HIGH |
| G-03 | `llm` (factory behavior, `extract_json` edge cases, provider clients mocked) | Provider abstraction untested | MED |
| G-04 | `vector_store` (add/query/delete/structure, fallback backend parity) | Store interface untested | MED |
| G-05 | `embeddings` (hashing provider determinism, factory fallback) | Embedding contract untested | MED |
| G-06 | Integration: rebuild → analyze → RAG evidence → history row | End-to-end contract | HIGH (regression net for Phase 4) |
| G-07 | Adversarial payloads (prompt injection attempts, XSS strings) | Security regression tests | MED |
| G-08 | Concurrency smoke (parallel analyses) | Thread-safety evidence | MED |

### 13.3 Required structure

- Unit: one file per module (align with Phase 2 splits).
- Integration: `tests/integration/test_pipeline.py`, `tests/integration/test_rebuild.py`.
- E2E smoke: `scripts/smoke_test.py` (start server, hit health/analyze/pages, exit code gate).

---

## 14. Documentation Review

### 14.1 Status matrix

| Document | Verdict | Action |
|---|---|---|
| `docs/PRD.md` | Current | Keep |
| `docs/System_Design_Document.md` | Current | Keep |
| `docs/Repository_Audit.md` | New (this phase) | Keep |
| `docs/Migration_Plan.md` | New (this phase) | Keep |
| `docs/Technical_Debt_Report.md` | New (this phase) | Keep |
| `docs/Implementation_Roadmap.md` | New (this phase) | Keep |
| `docs/architecture.md` | Current (Phase 2 update) | Keep |
| `docs/ml_pipeline.md` | **Needs update** | Add calibration note; intent stage in pipeline diagram |
| `docs/rag_pipeline.md` | Needs minor update | TTL cache, invalidate-on-rebuild |
| `docs/api.md` | **Outdated** | Add `intent`, `risk_score`, CRITICAL/UNCERTAIN, 503 semantics |
| `docs/setup.md` | Current | Keep; add requirements-split note (R-02) |
| `README.md` | **Needs update** | V2 features (intent, 5-level risk), docs table links |
| — | **Missing** | `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE` (choose open-source license), `.github/` workflows |

### 14.2 Documentation debt summary

| Severity | Items |
|---|---|
| HIGH | `docs/api.md` out of sync with V2 response fields |
| MED | `README.md` feature list, `ml_pipeline.md`/`rag_pipeline.md` minor |
| LOW | Missing CHANGELOG/CONTRIBUTING/LICENSE |

---

## Document control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 2.0 | TBD | TextShield Architecture team | Technical debt, dependency, API, DB, frontend, testing, documentation reviews |