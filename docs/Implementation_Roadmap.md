# TextShield V2.0 — Implementation Roadmap

**Phase:** 3 — Repository Audit & Refactoring Plan
**Scope:** Steps 6 (Missing Components), 15 (Risk Assessment), 16 (Final Migration Roadmap)

---

## 6. Missing Components

Inventory of components from the PRD/SDD that do not yet exist as formal artifacts, with the delta from the current implementation.

| Component | Current state | Gap | Required work | Priority |
|---|---|---|---|---|
| Semantic Analysis Engine | Implemented across `preprocess.py`, `classifier.py`, `intent.py` | No formal facade | Optional thin facade `nlp_service`; not required | LOW |
| Intent Analysis Engine | **Present** (`app/ml/intent.py`, 8 classes) | None | None — done in Phase 2 | — |
| Behavior Analysis Engine | **Present** (`app/ml/indicators.py`) | None | None | — |
| Entity Extraction Engine | **Present** (extractors in `preprocess.py`) | None | None | — |
| Embedding Service | **Present** (`app/rag/embeddings.py`, 2 providers) | None | None | — |
| Knowledge Base | **Present** (33 docs, 10 categories) | `reference/` category planned but absent | Add reference material; enrich docs | LOW |
| Vector Database | **Present** (chromadb + numpy fallback) | None | None | — |
| RAG Pipeline | **Present** (index/embed/retrieve/generate) | None | None | — |
| Evidence Validation Engine | Partial: retriever returns real chunks; generator validates JSON | No dedicated validation helper | New `app/rag/evidence.py` (T-03/Phase 3) | MED |
| Decision Engine | **Present** (`risk_engine.py`, 5 levels, factors) | None | None | — |
| Confidence Engine | Partial: calibrated probability + calibration report | No runtime exposure of calibration quality | Model Manager exposes metrics (Phase 3) | MED |
| Risk Engine | **Present** | None | None | — |
| Recommendation Engine | Present inside `generator._recommendation` | Cohesion | Split into `services/recommendation.py` (Phase 2) | MED |
| Analytics Service | **Present** (`aggregate_stats`) | No intent distribution | After DB-01 (Phase 4) | LOW |
| History Service | **Present** | No `intent` column | DB-01 (Phase 4) | MED |
| Model Manager | Partial: `classifier.py` loads artifacts; `/api/model-info` reads metadata | No formal component | New `services/model_manager.py` (Phase 3) | MED |
| Settings screen | Absent (by design — env config) | — | Planned future page | FUTURE |
| System logs table | Absent | — | Phase 9 | FUTURE |

**Key message:** no *core* component is missing. The remaining gaps are formalization (evidence validation, model manager, confidence exposure), schema evolution (intent column), and future-scope surfaces (settings/logs).

---

## 15. Risk Assessment (migration)

Rating: **L** low, **M** medium, **H** high.

| # | Risk | Rating | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Behavior drift during refactors (step-splitting, router split, schema split) | M | Silent regressions | Refactor-transaction rule: run full suite (93 tests) after every refactor step; add integration tests first |
| R-02 | SQLite schema migration breaks existing `textshield.db` | M | History loss / startup failure | Idempotent `ALTER TABLE` guarded by `PRAGMA table_info`; back up DB before migrating; test on the real DB file |
| R-03 | New modules (`evidence.py`, `model_manager.py`) create circular imports | L | Import-time crashes | Dependency-direction rule: services → rag/ml; run `compileall` + suite; keep factories lazy |
| R-04 | Frontend changes degrade UX/accessibility | L | Usability regressions | Manual smoke checklist; keep classes intact; incremental JS extraction |
| R-05 | Test suite runtime grows (embedding loads per session) | M | Slow CI feedback | Fixture-scope session caching in `conftest.py`; split fast/slow marks |
| R-06 | Docs and implementation drift during migration | L | Misleading docs | Docs aligned in Phase 5 *after* code phases; doc checklist in PR template |
| R-07 | Committing Phase 2 work + docs together pollutes history | L | History clarity | Separate commits: (1) Phase 2 code, (2) phase-3 docs, (3) each migration phase |
| R-08 | Optional-dependency handling (chromadb/sentence-transformers absent) | M | RAG degraded on other machines | Keep fallbacks; CI matrix with `--no-rag` marker test |
| R-09 | Prompt-injection regressions after generator refactor | M | Misleading explanations | Adversarial test payloads; verdict-independence invariant test |
| R-10 | Scope creep into future items (settings screen, microservices) | H | Delays | Roadmap freeze: future items only after Phase 10 sign-off |

---

## 16. Final Migration Roadmap

Ordering rule: **behavior-preserving first, data changes second, docs third, hardening last** — every step leaves the system shippable and the suite green.

### Phase 0 — Baseline (now)

| Item | Detail |
|---|---|
| Commit Phase 2 work | `git add` 10 modified + 3 new files; message per repo style |
| Tag V1.2 checkpoint (optional) | Pre-migration recoverable point |
| Gate | `pytest` green (93), compileall green |

### Phase 1 — Repository hygiene

| Item | Detail |
|---|---|
| Add `.pytest_cache`/`.ruff_cache` to `.gitignore` | |
| Add `pyproject.toml` (packaging + ruff config) | |
| Add `requirements-dev.txt` (ruff, pytest-cov) | |
| Add `.github/workflows/ci.yml` (lint + test) | |
| **Gate** | CI passes on clean clone |

### Phase 2 — Low-risk refactors (one commit per refactor)

Commit A: extract `analysis_service` step functions.
Commit B: split `schemas/analysis.py` into 3 modules.
Commit C: split KB router → `routes_knowledge.py`.
Commit D: extract `services/recommendation.py` from generator.
Commit E: extract `static/js/common.js`.
**Gate:** suite green after every commit; zero behavior change.

### Phase 3 — Formal surfaces

Commit F: `app/rag/evidence.py` (validation helpers) wired into retriever/generator.
Commit G: `app/services/model_manager.py`; classifier + `/api/model-info` use it (expose calibration metrics).
**Gate:** `test_rag`, `test_classifier`, `test_api` green; new `test_evidence.py` added.

### Phase 4 — Schema evolution

Commit H: idempotent migration — `analyses.intent` column (+ index on `risk_level`); record assembly into `database.py`; history API `intent` filter; stats `intent_distribution`.
Commit I (optional): `kb_metadata` table mirroring `structure.json`.
**Gate:** migration on existing DB verified; `test_database.py` added.

### Phase 5 — Documentation alignment

Commit J: `docs/api.md` V2 fields; README V2 features; `ml_pipeline.md`/`rag_pipeline.md` updates; `CHANGELOG.md` created; add `LICENSE` + `CONTRIBUTING.md` (choose license).
**Gate:** doc review checklist; PRD AC-20 satisfied.

### Phase 6 — Frontend polish

Commit K: accessibility pass (focus/aria keyboards), active nav, empty/loading states, intent column/filter on History, intent chart on Analytics.
**Gate:** manual smoke checklist + existing API tests.

### Phase 7 — Testing hardening

Commit L: unit tests — `test_generator`, `test_database`, `test_llm`, `test_vector_store`, `test_embeddings`, `test_evidence`.
Commit M: integration tests — pipeline, rebuild→analyze→evidence; adversarial payloads; concurrency smoke.
Commit N: `scripts/smoke_test.py` + CI job.
**Gate:** coverage report ≥ target (set baseline in Phase 1); suite green.

### Phase 8 — Performance

Commit O: optional result cache (message-hash key, TTL); `/api/stats` 30 s cache; profiling report in docs.
**Gate:** latency budget ≤5 s CPU-only sustained (measured via smoke script).

### Phase 9 — Operational readiness

Commit P: `system_logs` table + startup health report; LAN-bind warning; graceful shutdown; `pip install .` packaging verification.
**Gate:** fresh venv install + smoke passes.

### Phase 10 — V2.0 release

Commit Q: tag `v2.0`; README badges; final doc pass; PRD acceptance checklist sign-off.
**Gate:** all PRD AC-01..AC-20 verifiable.

### Roadmap summary

| Phase | Focus | Complexity | Depends on | Risk |
|---|---|---|---|---|
| 0 | Baseline commit | L | — | — |
| 1 | Hygiene + CI | L | 0 | R-07 |
| 2 | Behavior-preserving refactors | M | 1 | R-01 |
| 3 | Evidence + Model Manager | M | 2 | R-03 |
| 4 | Schema evolution | M | 3 | R-02 |
| 5 | Docs alignment | L | 2–4 | R-06 |
| 6 | Frontend polish | M | 2 | R-04 |
| 7 | Testing hardening | M | 2–4 | R-05 |
| 8 | Performance | M | 7 | low |
| 9 | Operations | M | 4, 7 | low |
| 10 | Release | L | all | R-10 |

**Safest sequence principle:** never combine a data migration (4) with a refactor (2) in one commit; never document before code stabilizes; run the full suite and compileall after every single commit; keep every phase independently shippable.

---

## Document control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 2.0 | TBD | TextShield Architecture team | Missing components, risk matrix, prioritized migration roadmap |