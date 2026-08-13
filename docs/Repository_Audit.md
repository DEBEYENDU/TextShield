# TextShield V2.0 — Repository Audit

**Phase:** 3 — Repository Audit & Refactoring Plan
**Audience:** Engineering, Architecture review
**Scope:** Step 1 (Repository Analysis) and Step 2 (Module Inventory) of the migration plan

---

## 1. Repository Analysis

### 1.1 Snapshot

| Metric | Value |
|---|---|
| Repository root | `C:\Users\GOD KAKAROT\TextShield` |
| Git | Initialized, branch `main`, single commit `8a5c752` (V1.0 complete) |
| Working tree | Phase 2 (V2.0 intent/risk) changes **uncommitted** |
| Source files (Python) | ~45 files |
| Total code volume | ≈ 5,751 lines (app + scripts + tests + static + templates) |
| Test functions | 85 (93 tests passing: 76 V1 + 17 V2.0 additions) |
| API endpoints | 14 route paths (9 API + 5 pages) |
| Database | SQLite, single `analyses` table + 2 indexes |
| Vector store | ChromaDB (built), with numpy fallback backend |
| ML artifacts | Linear SVM via `CalibratedClassifierCV` (joblib) + metadata + evaluation report |
| Knowledge base | 33 markdown documents across 10 categories |

### 1.2 Folder structure (current)

```
TextShield/
├── run.py                       # uvicorn entry point
├── requirements.txt             # pinned-ish dependency set
├── pytest.ini                   # pytest config + warning filters
├── .env.example                 # documented configuration contract
├── .gitignore
├── README.md
├── app/
│   ├── main.py                  # FastAPI app assembly
│   ├── core/                    # config.py, logging.py
│   ├── schemas/                 # analysis.py (all Pydantic models)
│   ├── api/                     # 4 routers
│   ├── services/                # analysis_service.py, risk_engine.py
│   ├── ml/                      # preprocess, features, classifier, indicators,
│   │                            #   intent, url_analyzer, input_detection
│   ├── rag/                     # embeddings, vector_store, retriever, llm, generator
│   ├── database/                # database.py, models.py
│   ├── templates/               # 6 Jinja2 pages
│   └── static/                  # css/style.css, js/* (5 scripts)
├── scripts/                     # 4 lifecycle scripts
├── models/                      # joblib artifacts + JSON (gitignored)
├── vector_db/                   # chromadb + structure.json (gitignored)
├── knowledge_base/              # 10 category directories, 33 docs
├── data/
│   ├── raw/sample_sms_dataset.csv
│   ├── processed/               # train/test/dataset CSVs + dataset_info.json
│   └── README.md
├── logs/                        # textshield.log
├── tests/                       # 8 test modules + conftest.py
└── docs/                        # PRD, SDD, api, architecture, ml/rag pipeline, setup
```

### 1.3 Architecture summary (as-built)

The repository already implements the SDD's layered design:

1. **Frontend** — server-rendered Jinja2 pages + vanilla JS, no CDNs, single stylesheet. Pages: Analyze (3 tabs), History, Analytics, Knowledge Base, About.
2. **API layer** — FastAPI routers (`routes_analysis`, `routes_history`, `routes_stats`, `routes_health`) with Pydantic validation and structured error mapping (422/500/503).
3. **Orchestration** — `analysis_service.analyze()` runs the full pipeline deterministically.
4. **Domain engines** — ML classifier (TF-IDF + calibrated Linear SVM), indicator engine (15+ rules), intent engine (8 classes), URL analyzer (static), input detector (raw-email parsing).
5. **RAG stack** — embedding provider abstraction (sentence-transformers / hashing fallback), vector store abstraction (chromadb / numpy fallback), TTL-cached retriever, LLM provider abstraction (ollama / OpenAI-compatible), grounded explanation generator with template fallback.
6. **Decision engine** — `risk_engine.py` produces score + 5 levels (LOW/MEDIUM/HIGH/CRITICAL/UNCERTAIN) with transparent factors; CRITICAL/UNCERTAIN rules per PRD §20.
7. **Persistence** — SQLite `analyses` table (hashed content by default), thread-safe access, aggregate stats.
8. **Lifecycle scripts** — dataset preparation, training, evaluation, knowledge-base build.

### 1.4 Key structural observations

| Observation | Detail |
|---|---|
| Architecture matches SDD | Layered design already in place; the gap is **depth**, not **shape** |
| V2.0 features partially present | Intent engine, 5-level risk, `intent`/`risk_score` in responses, CRITICAL/UNCERTAIN semantics implemented in Phase 2 |
| Uncommitted work | Phase 2 changes not yet committed (10 modified + 3 new files) |
| Data artifacts present | `data/processed/*.csv` and `textshield.db` exist on disk (gitignored) |
| Docs split | V1 docs (`api.md`, `ml_pipeline.md`, `rag_pipeline.md`, `setup.md`) predate V2.0 fields; PRD + SDD are new |
| No CI | No GitHub Actions / lint / type-check configuration |
| No packaging | No `pyproject.toml`/`setup.cfg`; dependencies only in `requirements.txt` |

---

## 2. Module Inventory

Legend — **Quality:** A = clean, B = good, C = acceptable, D = needs work. **Complexity:** L/M/H. **Reusability:** High/Medium/Low (in-repo).

### 2.1 Backend core

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/main.py` | App assembly | FastAPI app, routers, static/template mounting, startup events | FastAPI, routers, config | B | L | Medium |
| `app/core/config.py` | Configuration singleton | `.env` loading, typed settings, path resolution, directory bootstrap | dotenv, pathlib | A | L | High |
| `app/core/logging.py` | Structured logging | Logger factory, levels, formats | stdlib logging | B | L | High |
| `app/schemas/analysis.py` | API contracts | All request/response Pydantic models + validators | pydantic, config | A | L | High |

### 2.2 API layer

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/api/routes_analysis.py` | Analysis endpoint | `POST /api/analyze`, exception→HTTP mapping | schemas, analysis_service | A | L | High |
| `app/api/routes_history.py` | History endpoints | List / delete one / clear all | database | B | L | High |
| `app/api/routes_stats.py` | Stats + model info | `GET /api/stats`, `GET /api/model-info` | database, classifier, config | B | L | High |
| `app/api/routes_health.py` | Health + KB endpoints | `GET /api/health`, KB status, rebuild | retriever, db, build script | B | M | Medium |

### 2.3 Services

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/services/analysis_service.py` | Pipeline orchestrator | Input parsing/auto-detection, evidence stages, risk, explanation, history, result mapping | all ml/rag/db/schemas | B | H | High |
| `app/services/risk_engine.py` | Decision engine | Score computation, 5-level mapping, CRITICAL/UNCERTAIN rules, factors | config, ml.intent | A | M | High |

### 2.4 ML domain

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/ml/preprocess.py` | Text preparation | Normalization, placeholder redaction, entity extractors, optional tokenize | stdlib re | A | M | High |
| `app/ml/features.py` | Feature building | Corpus prep, TF-IDF builder (single source of truth) | sklearn, preprocess | A | L | High |
| `app/ml/classifier.py` | Model runtime | Lazy artifact load, predict, metadata | joblib, sklearn, config | B | M | High |
| `app/ml/indicators.py` | Behavior rules | 15+ regex/lexical rules + structural checks, severity sort | re, preprocess | B | M | High |
| `app/ml/intent.py` | Intent engine (V2) | 8 intent classes, ordered matching, evidence | re | A | M | High |
| `app/ml/url_analyzer.py` | Static URL analysis | Scheme/host/TLD/IP/shortener/look-alike checks, sender-domain analysis | re, urllib.parse | B | M | High |
| `app/ml/input_detection.py` | Input type handling | Raw-email detection + stdlib parsing | stdlib email | B | L | High |

### 2.5 RAG domain

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/rag/embeddings.py` | Embedding abstraction | Provider interface, sentence-transformers + hashing providers, factory | numpy, sentence-transformers | B | M | High |
| `app/rag/vector_store.py` | Vector store abstraction | Store interface, chromadb + numpy backends, structure metadata | chromadb, numpy | B | M | High |
| `app/rag/retriever.py` | Retrieval service | Embed→search→shape evidence, TTL-cached status, cache invalidation | embeddings, vector_store, config | A | M | High |
| `app/rag/llm.py` | LLM abstraction | Client interface, ollama + OpenAI-compat, factory, JSON extraction | requests, config | B | M | Medium |
| `app/rag/generator.py` | Explanation engine | Grounded prompt, LLM call, JSON validation, template fallback, recommendations | llm, config | B | M | High |

### 2.6 Persistence

| File | Purpose | Responsibilities | Dependencies | Quality | Complexity | Reusability |
|---|---|---|---|---|---|---|
| `app/database/database.py` | SQLite access | Schema DDL, thread-safe connections, insert/query/delete/clear/stats | stdlib sqlite3, config | A | M | High |
| `app/database/models.py` | Record types | `AnalysisRecord` dataclass | dataclasses | A | L | High |

### 2.7 Frontend

| File | Purpose | Responsibilities | Quality | Complexity | Reusability |
|---|---|---|---|---|---|
| `app/templates/base.html` | Layout shell | Nav, theme, footer, script/css blocks | Jinja2 | B | L | High |
| `app/templates/index.html` | Analyze screen | 3 tabs, form, result/error containers | Jinja2 | B | L | High |
| `app/templates/history.html` | History screen | Table + filters + pagination skeleton | Jinja2 | B | L | Medium |
| `app/templates/analytics.html` | Analytics screen | Chart containers + model-info panels | Jinja2 | B | L | Medium |
| `app/templates/knowledge_base.html` | KB screen | Category/document/rebuid skeleton | Jinja2 | B | L | Medium |
| `app/templates/about.html` | About screen | Architecture/privacy/model content | Jinja2 | B | L | Medium |
| `static/js/index.js` | Analyze logic | Payload build, fetch, render verdict/evidence, tabs | — | B | M | Medium |
| `static/js/history.js` | History logic | Fetch/render/filter/delete/clear | — | B | M | Medium |
| `static/js/analytics.js` | Analytics logic | Stats fetch, canvas charts, model info | — | B | M | Medium |
| `static/js/kb.js` | KB logic | Browse + rebuild | — | B | M | Low |
| `static/js/about.js` | About logic | Health/model fetch | — | B | L | Low |
| `static/css/style.css` | Styling | Theme, layout, badges, chips, cards, charts | — | B | M | High |

### 2.8 Lifecycle scripts

| File | Purpose | Responsibilities | Quality | Complexity | Reusability |
|---|---|---|---|---|---|
| `scripts/prepare_dataset.py` | Data prep | Raw→processed CSV validation, train/test split | pandas | B | M | Medium |
| `scripts/train_model.py` | Training | Candidate algorithms, CV selection, calibration, artifact persistence, metadata | sklearn, joblib, app.ml | B | H | Medium |
| `scripts/evaluate_model.py` | Evaluation | Metrics, confusion matrix, calibration report | sklearn, joblib | B | M | Medium |
| `scripts/build_knowledge_base.py` | KB indexing | Discover, chunk, embed, store, structure metadata | app.rag | B | M | High |

### 2.9 Tests

| File | Coverage target | Tests | Quality |
|---|---|---|---|
| `tests/conftest.py` | Fixtures; auto-training model when artifacts missing | — | A |
| `tests/test_preprocessing.py` | Normalization, redaction, placeholders, stopwords | 9 | A |
| `tests/test_classifier.py` | Predict path, model info | 6 | A |
| `tests/test_indicators.py` | Rule triggers, severities | 9 | A |
| `tests/test_intent.py` | 8 intent classes, precedence | 10 | A |
| `tests/test_url_analyzer.py` | URL patterns, domain checks | 8 | A |
| `tests/test_risk.py` | Levels, CRITICAL/UNCERTAIN rules, factors | 15 | A |
| `tests/test_rag.py` | Retrieval, status, fallback behavior | 10 | A |
| `tests/test_api.py` | Endpoints, validation, raw-email detection, V2 fields | 18 | B |

### 2.10 Documentation

| Document | Status | Content |
|---|---|---|
| `docs/PRD.md` | Current (V2.0) | Full requirements |
| `docs/System_Design_Document.md` | Current (V2.0) | Full design blueprint |
| `docs/architecture.md` | Updated (Phase 2) | Topology, modules, pipeline |
| `docs/ml_pipeline.md` | Needs minor update | V1-era, still accurate |
| `docs/rag_pipeline.md` | Needs minor update | V1-era, still accurate |
| `docs/api.md` | **Outdated** | Missing V2 fields (`intent`, `risk_score`) and CRITICAL/UNCERTAIN |
| `docs/setup.md` | Current | Install/config/operation |
| `README.md` | Needs update | V1 feature list; missing V2 intent/5-level risk |

### 2.11 Inventory summary

- **46 Python modules** across app (31), scripts (4), tests (9), entry (2).
- **6 templates**, **5 JS modules**, **1 stylesheet**.
- **33 knowledge documents** in 10 categories.
- **4 configuration artifacts**: `.env.example`, `pytest.ini`, `requirements.txt`, `.gitignore`.
- No dead or orphaned source files found; all modules are reachable from `app.main` or `scripts` or `tests`.

---

## Document control

| Version | Date | Author | Change summary |
|---|---|---|---|
| 2.0 | TBD | TextShield Architecture team | Initial repository audit for Phase 3 |