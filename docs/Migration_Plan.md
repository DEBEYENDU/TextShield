# TextShield V2.0 — Migration Plan

**Phase:** 3 — Repository Audit & Refactoring Plan
**Scope:** Steps 3 (Architecture Comparison), 4 (Reuse Analysis), 7 (Migration Strategy), 9 (Folder Structure Proposal)

---

## 3. Architecture Comparison (current → target)

Legend — **Compatibility:** ✓ full, ◐ partial, ✗ none.

| Existing module | Target module (SDD §6) | Compatibility | Required changes |
|---|---|---|---|
| `app/core/config.py` | Configuration layer | ✓ | Add planned keys (risk thresholds already added); consider freeze via dataclass |
| `app/core/logging.py` | Cross-cutting | ✓ | None |
| `app/schemas/analysis.py` | Schema layer | ✓ | Add optional `intent` column to history (design target) |
| `app/api/*` (4 routers) | Controllers | ✓ | Extend history filters (intent); keep exception map |
| `app/services/analysis_service.py` | Orchestration service | ✓ | Extract step-level functions for testability (split per §4) |
| `app/services/risk_engine.py` | Decision engine | ✓ (V2 done) | None major; document weights in `docs/api.md` |
| `app/ml/preprocess.py` | Semantic preprocessing | ✓ | None |
| `app/ml/features.py` | Feature builder | ✓ | None |
| `app/ml/classifier.py` | Model Manager (runtime half) | ◐ | Add metadata surface: expose calibration info, feature count |
| `app/ml/indicators.py` | Behavior Analysis Engine | ✓ | None (V2 complete) |
| `app/ml/intent.py` | Intent Analysis Engine | ✓ (V2 new) | None |
| `app/ml/url_analyzer.py` | Entity/URL analysis | ✓ | None |
| `app/ml/input_detection.py` | Input handling | ✓ | None |
| `app/rag/embeddings.py` | Embedding Service | ✓ | None |
| `app/rag/vector_store.py` | Vector Database | ✓ | None |
| `app/rag/retriever.py` | Evidence Validation (retrieval half) | ✓ | Add explicit `validate_evidence()` helper (formal evidence-validation surface) |
| `app/rag/llm.py` | LLM Integration | ✓ | None |
| `app/rag/generator.py` | Explainability + Recommendation Engine | ✓ | Extract `recommendation` builder into own module (split per §4) |
| `app/database/database.py` | History + Analytics Service | ◐ | Add `intent` column; add `kb_metadata`, `app_settings`, `system_logs` (design targets) |
| `app/database/models.py` | Repository types | ✓ | Extend record with `intent` |
| `app/templates/*` | Frontend | ✓ | Accessibility pass; settings panel placeholder |
| `static/js/*` | Frontend logic | ✓ | Extract shared rendering helpers (escapeHtml, fetch wrapper) |
| `scripts/train_model.py` | Model Manager (build half) | ✓ | None |
| `scripts/build_knowledge_base.py` | Knowledge Base indexing | ✓ | None |
| **—** | Evidence Validation Engine (formal) | ✗ | New thin module or enriched retriever helpers |
| **—** | Confidence Engine (formal) | ✗ | New wrapper around calibration metadata + runtime probability |
| **—** | Settings screen | ✗ | Frontend page (future) |

**Bottom line:** the current tree already realizes ~90% of the SDD. Migration is about *hardening, formalizing missing surfaces, and closing debt* — not rebuilding.

---

## 4. Reuse Analysis

Decision per module with justification.

### 4.1 KEEP (as-is; mature, tested)

| Module | Justification |
|---|---|
| `app/ml/preprocess.py` | Stable, unit-tested, no churn since V1 |
| `app/ml/features.py` | Single source of truth for vectorizer |
| `app/ml/intent.py` | New (Phase 2), fully tested |
| `app/ml/indicators.py` | Mature rule engine; extensions happen by data (rule dicts) |
| `app/ml/url_analyzer.py` | Static-only by design (SSRF-free) |
| `app/ml/input_detection.py` | Tested parsing path |
| `app/services/risk_engine.py` | Deterministic, unit-tested; PRD rules implemented |
| `app/rag/embeddings.py` | Interface + fallback proven |
| `app/rag/vector_store.py` | Interface + fallback proven |
| `app/rag/retriever.py` | TTL cache + invalidation tested |
| `app/rag/llm.py` | Provider abstraction proven |
| `app/core/config.py`, `app/core/logging.py` | Cross-cutting, stable |
| `app/database/database.py` | Thread-safe, parameterized |
| `scripts/*` (all 4) | Lifecycle pipeline proven end-to-end |
| `tests/*` (all 9) | 93 passing tests; keep as regression net |

### 4.2 REFACTOR (keep behavior, restructure internals)

| Module | Refactor scope | Why | Risk |
|---|---|---|---|
| `app/services/analysis_service.py` | Split `analyze()` (229 lines) into private step functions (`_run_ml`, `_run_evidence`, `_build_payload`) or a small pipeline class | Improves unit-testability and mirrors SDD stages; large function debt | Low if behavior-preserving |
| `app/rag/generator.py` | Extract `_recommendation` into `app/services/recommendation.py` | Separates decision-adjacent logic from explanation formatting (cohesion) | Low |
| `app/api/routes_health.py` | Split KB routes into `routes_knowledge.py` | Health and KB are different concerns in one router | Low |
| `app/schemas/analysis.py` | Split response models into `schemas/history.py` + `schemas/system.py` | Single file grows; keeps contracts organized | Low |
| `static/js/index.js` | Extract `escapeHtml`, fetch helper, chip/badge renderers into `static/js/common.js` | DRY across 5 scripts | Low |
| `tests/test_api.py` | Split into `test_api_analysis.py` + `test_api_history.py` | Parallel-izable, clearer failures | Low |

### 4.3 MERGE

| Modules | Merge into | Why |
|---|---|---|
| `app/database/models.py` + record construction in `analysis_service._store_history` | Keep both but move record assembly into `database.py` | Single persistence responsibility |
| `app/rag/retriever.py` + evidence-shaping code | Keep; add `app/rag/evidence.py` for validation helpers | Formal Evidence Validation Engine (SDD) without duplicating retriever logic |

### 4.4 SPLIT

| Module | Split into | Why |
|---|---|---|
| `app/schemas/analysis.py` (134 lines, 8 models) | `schemas/analysis.py`, `schemas/history.py`, `schemas/system.py` | One concern per file |
| `app/ml/classifier.py` | Keep runtime; move metadata-loading to `app/services/model_manager.py` | Formal Model Manager per SDD; classifier stays thin |

### 4.5 REPLACE / REMOVE

| Item | Decision | Justification |
|---|---|---|
| None of the source modules | — | No module needs replacement or removal; all are reachable and used |

### 4.6 Disposition summary

| Decision | Count | Modules |
|---|---|---|
| KEEP | 25 | core(2), schemas(1), api(4), services(risk), ml(6), rag(4), database(2), scripts(4), tests(9 → counted as suite) |
| REFACTOR | 6 | analysis_service, generator, routes_health, schemas, index.js, test_api |
| MERGE | 2 pairs | db record assembly; evidence helpers |
| SPLIT | 3 | schemas, classifier/model-manager |
| REPLACE / REMOVE | 0 | — |

---

## 7. Migration Strategy

Ten sequential phases. Each phase is **behavior-preserving or additive**; the test suite (93 tests) is the regression gate at every step.

### Phase 1 — Repository cleanup

- **Objectives:** Commit Phase 2 work; enforce hygiene; add `.pytest_cache` to `.gitignore`; add CI skeleton (lint + test workflow); confirm `data/processed/*` and `textshield.db` stay untracked.
- **Files affected:** `.gitignore`, `requirements-dev.txt` (ruff, optionally), `.github/workflows/ci.yml` (new).
- **Expected outcome:** Clean tree, reproducible checks, no secrets/artifacts tracked.
- **Dependencies:** None.
- **Complexity:** Low. **Risks:** None material.

### Phase 2 — Backend restructuring (low-risk refactors)

- **Objectives:** Split `analysis_service.analyze()` into step functions; extract recommendation engine; split schemas; split KB router; extract `common.js`.
- **Files affected:** `analysis_service.py`, `generator.py`, `routes_health.py`, `schemas/*`, `routes_knowledge.py` (new), `static/js/*`.
- **Expected outcome:** Same behavior, smaller units, better test granularity.
- **Dependencies:** Phase 1.
- **Complexity:** Low–Medium. **Risks:** Behavior drift — mitigated by running the full suite after each refactor step.

### Phase 3 — Formal evidence & model surfaces

- **Objectives:** Add `app/rag/evidence.py` (evidence validation: non-empty, source/category present, score bounds, dedup); add `app/services/model_manager.py` (artifact load, metadata, calibration info) used by classifier and `/api/model-info`.
- **Files affected:** new modules + `retriever.py`, `classifier.py`, `routes_stats.py`.
- **Expected outcome:** Evidence Validation Engine and Model Manager per SDD §6.
- **Dependencies:** Phase 2.
- **Complexity:** Medium. **Risks:** Regression in retrieval paths — covered by `test_rag.py`.

### Phase 4 — Schema evolution (history)

- **Objectives:** Add `intent` column to `analyses` (nullable, backfill from live analyses); add `kb_metadata` table mirroring `structure.json`; migration via `ALTER TABLE ... ADD COLUMN` guarded by pragma check.
- **Files affected:** `database.py`, `models.py`, `analysis_service.py`, `test_api.py`.
- **Expected outcome:** Intent analytics possible; KB status without disk reads.
- **Dependencies:** Phase 3.
- **Complexity:** Medium. **Risks:** Old DB files need migration guard — mitigated by idempotent migration at init.

### Phase 5 — Documentation alignment

- **Objectives:** Update `docs/api.md` (intent, risk_score, CRITICAL/UNCERTAIN, 422/503 semantics), `README.md` (V2 features), `ml_pipeline.md`/`rag_pipeline.md` touch-ups; add `CHANGELOG.md`.
- **Files affected:** `docs/*`, `README.md`.
- **Expected outcome:** Docs match implementation (PRD AC-20).
- **Dependencies:** Phases 2–4 (so docs describe reality).
- **Complexity:** Low. **Risks:** Doc/code drift later — mitigate with doc-review checklist in CI PR template.

### Phase 6 — Frontend polish

- **Objectives:** Accessibility pass (focus states, aria labels, color-independent verdicts), active-nav highlighting, empty/loading states, settings-panel placeholder; shared `common.js`.
- **Files affected:** templates, `static/css/style.css`, `static/js/*`.
- **Expected outcome:** NFR-09/10 alignment.
- **Dependencies:** Phase 2.
- **Complexity:** Medium. **Risks:** Visual regressions — mitigated by manual smoke checklist.

### Phase 7 — Testing hardening

- **Objectives:** Add unit tests: `test_generator.py` (template determinism, recommendation matrix), `test_database.py`, `test_llm.py` (mock), `test_vector_store.py`, `test_embeddings.py`, `test_evidence.py`; integration: rebuild → analyze → evidence flow; smoke script `scripts/smoke_test.py`.
- **Files affected:** `tests/*` (new modules), `pytest.ini`.
- **Expected outcome:** Coverage of every module; CI-runnable.
- **Dependencies:** Phases 2–4.
- **Complexity:** Medium. **Risks:** Slow suite (embedding load) — mitigated by fixture caching.

### Phase 8 — Performance tuning

- **Objectives:** Profile pipeline; embed-status cache (done); add optional per-analysis result cache keyed by message hash; bound RAG query latency.
- **Files affected:** `retriever.py`, `analysis_service.py`, `config.py`.
- **Expected outcome:** Sustained ≤5 s CPU-only analyses under load.
- **Dependencies:** Phase 7 (baseline).
- **Complexity:** Medium. **Risks:** Cache invalidation bugs — mitigated by hash + config TTL.

### Phase 9 — Operational polish

- **Objectives:** `system_logs` table (rotated writes), startup health checks, graceful shutdown, LAN-bind warning, `pyproject.toml` packaging for `pip install .`.
- **Files affected:** `database.py`, `main.py`, new `pyproject.toml`.
- **Expected outcome:** Operable beyond the dev laptop.
- **Dependencies:** Phases 4, 7.
- **Complexity:** Medium. **Risks:** Packaging conflicts — mitigated by venv test install.

### Phase 10 — Release & V2.0 sign-off

- **Objectives:** Full suite + smoke + docs review; tag `v2.0`; update README badges; squash-commit plan.
- **Files affected:** none (process).
- **Expected outcome:** PRD acceptance criteria met; shippable.
- **Dependencies:** All prior phases.
- **Complexity:** Low. **Risks:** Scope drift into future scope — guarded by PRD §9.

---

## 9. Folder Structure Proposal

### 9.1 Target structure (additions/moves in **bold**)

```
TextShield/
├── run.py
├── pyproject.toml                      ← NEW (packaging + lint config)
├── requirements.txt
├── requirements-dev.txt                ← NEW (ruff, coverage)
├── pytest.ini
├── .env.example
├── .gitignore                          ← UPDATED (.pytest_cache, .ruff_cache)
├── CHANGELOG.md                        ← NEW
├── README.md                           ← UPDATED (V2 features)
├── .github/workflows/ci.yml            ← NEW
├── app/
│   ├── main.py
│   ├── core/        (config, logging)            — KEEP
│   ├── schemas/
│   │   ├── analysis.py                            — KEEP (request + result)
│   │   ├── history.py                             ← SPLIT from analysis.py
│   │   └── system.py                              ← SPLIT from analysis.py
│   ├── api/
│   │   ├── routes_analysis.py                     — KEEP
│   │   ├── routes_history.py                      — KEEP
│   │   ├── routes_stats.py                        — KEEP
│   │   ├── routes_health.py                       — KEEP (health only)
│   │   └── routes_knowledge.py                    ← SPLIT from routes_health.py
│   ├── services/
│   │   ├── analysis_service.py                    — KEEP (step-functions refactor)
│   │   ├── risk_engine.py                         — KEEP
│   │   ├── recommendation.py                      ← SPLIT from generator.py
│   │   └── model_manager.py                       ← NEW (formal Model Manager)
│   ├── ml/        (preprocess, features, classifier, indicators,
│   │               intent, url_analyzer, input_detection)  — KEEP
│   ├── rag/
│   │   ├── embeddings.py, vector_store.py,
│   │   │   retriever.py, llm.py, generator.py     — KEEP
│   │   └── evidence.py                            ← NEW (Evidence Validation Engine)
│   ├── database/
│   │   ├── database.py                            — KEEP (+ intent col, new tables)
│   │   └── models.py                              — KEEP (+ intent field)
│   ├── templates/     (6 pages)                   — KEEP (+ settings placeholder)
│   └── static/
│       ├── css/style.css                          — KEEP
│       └── js/ (common.js, index.js, history.js,
│                analytics.js, kb.js, about.js)    — common.js NEW
├── scripts/        (4 scripts)                    — KEEP (+ smoke_test.py NEW)
├── models/         (gitignored)                   — KEEP
├── vector_db/      (gitignored)                   — KEEP
├── knowledge_base/ (10 categories)                — KEEP
├── data/           (raw, processed)               — KEEP
├── logs/                                           — KEEP
├── tests/          (9 modules → ~15)              — KEEP + EXPAND
└── docs/           (PRD, SDD, audit, plan, debt,
                     roadmap, api, architecture,
                     ml/rag pipeline, setup)       — KEEP + ALIGN
```

### 9.2 Folder decisions

| Folder | Decision | Note |
|---|---|---|
| `app/` | Keep | Package root; organized by concern |
| `app/schemas/` | Split into 3 files | Contract clarity |
| `app/api/` | Add `routes_knowledge.py` | Router per concern |
| `app/services/` | Add 2 modules | Formal SDD surfaces |
| `app/rag/` | Add `evidence.py` | Formal evidence validation |
| `static/js/` | Add `common.js` | DRY across pages |
| `scripts/` | Add `smoke_test.py` | CI-ready end-to-end check |
| `models/`, `vector_db/`, `logs/`, `data/processed/` | Runtime-only | Stay gitignored |
| `.pytest_cache/` | Clean or ignore | Add to `.gitignore` |

### 9.3 Deprecated / not needed

- No existing folder is deprecated; the `templates/` + `static/` split stays (no frontend framework introduced).
- `app/database/models.py` remains (merged conceptually with `database.py` responsibilities, no file removal).

---

## Document control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 2.0 | TBD | TextShield Architecture team | Initial migration plan for Phase 3 |