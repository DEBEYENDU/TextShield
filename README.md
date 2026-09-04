# TextShield

### AI-Powered Multichannel Spam & Ham Detection with RAG-Based Explainable Analysis

> **Detect Spam. Understand the Risk. Stay Protected.**

TextShield is a production-quality academic project that detects whether a
message is **SPAM** or **HAM** across three channels — **SMS, general text,
and email** — and explains every verdict using a three-layer architecture:

| Layer | Role | Technology |
|---|---|---|
| **ML classifier** | Primary spam/ham decision | TF-IDF + Linear SVM / NB / Logistic Regression (scikit-learn) |
| **RAG system** | Knowledge retrieval / evidence | ChromaDB + sentence-transformers (fallbacks included) |
| **LLM layer** | Explanation / reasoning / recommendation | Ollama, OpenAI-compatible or NVIDIA NIM (optional, with template fallback) |

The ML model **never depends** on RAG or the LLM: if those services are
offline the application still returns the classification, confidence and
indicators, and explains that the advanced service is unavailable.

---

## Table of Contents

- [1. Problem Statement](#1-problem-statement)
- [2. Project Objectives](#2-project-objectives)
- [3. Features](#3-features)
- [4. Architecture](#4-architecture)
- [5. Technologies](#5-technologies)
- [6. Project Structure](#6-project-structure)
- [7. Installation](#7-installation)
- [8. Dataset Setup](#8-dataset-setup)
- [9. Model Training](#9-model-training)
- [10. RAG Knowledge Base](#10-rag-knowledge-base)
- [11. LLM Setup](#11-llm-setup)
- [12. Running the Application](#12-running-the-application)
- [13. API Documentation](#13-api-documentation)
- [14. Threat Intelligence Platform](#14-threat-intelligence-platform)
- [15. Threat Intelligence Dashboard](#15-threat-intelligence-dashboard)
- [16. Screenshots](#16-screenshots)
- [17. ML Evaluation](#17-ml-evaluation)
- [18. Limitations](#18-limitations)
- [19. Future Scope](#19-future-scope)
- [20. Security Considerations](#20-security-considerations)
- [21. Running the Tests](#21-running-the-tests)
- [22. Documentation](#22-documentation)

---

## 1. Problem Statement

Email, SMS and chat channels are flooded with spam and fraud. A message like
*"Your bank account will be blocked. Verify immediately using this link"* looks
urgent, official, and asks for action — which is exactly why millions of people
fall for it every year.

An effective detection system must answer three questions:

1. **Is it spam?** — a reliable, fast, explainable classification.
2. **Why?** — visible evidence (patterns, URL tricks, similarity to known scams).
3. **What should I do?** — clear, actionable guidance.

Most academic spam projects stop at question 1. TextShield builds all three,
using a classical ML classifier for the decision, a Retrieval-Augmented
Generation (RAG) pipeline for evidence, and an LLM for explanation.

---

## 2. Project Objectives

- Classify SMS / text / email as SPAM or HAM with calibrated confidence.
- Compare at least three ML algorithms (Naive Bayes, Logistic Regression,
  Linear SVM) and select the best by F1-score and false-positive control.
- Detect rule-based spam indicators (urgency, prizes, OTP requests, job scams,
  delivery scams, banking phishing, ...) as supporting evidence.
- Perform safe, static URL analysis (shorteners, IP hosts, lookalike domains,
  suspicious TLDs) **without ever fetching the URL**.
- Build a RAG knowledge base (ChromaDB + sentence embeddings) and retrieve
  relevant scam-family evidence for every message.
- Generate explainable verdicts — via LLM when configured, via a deterministic
  template otherwise; the LLM explains, never overrides, the ML result.
- Provide a modern responsive dashboard: analyse, history, analytics,
  knowledge base, model information, threat intelligence dashboard.
- Expose a validated REST API with graceful degradation and logging.
- Be fully runnable on a student laptop, with zero required paid services.
- **Enterprise integration layer** (v2.1): stable APIs, SDKs, authentication,
  RBAC, plugin framework, event bus, webhooks, and batch processing.
- **Threat intelligence platform** (v2.2): IOC extraction, threat cache,
  async lookup engine, provider integrations, reputation aggregation,
  unified evidence integration, and a security analytics dashboard.

---

## 3. Features

### Core Detection
- **Multichannel input** — SMS, pasted text, structured email (subject/sender/body)
  and pasted raw email (auto-parsed with the stdlib `email` package).
- **Primary ML classification** — consistent train/serve preprocessing, saved
  model + vectorizer + metadata (joblib).
- **Indicator engine** — 15+ rule groups returning structured
  `{indicator, severity, category, evidence}` items.
- **Safe URL analysis** — static patterns only; cautious wording
  ("potentially suspicious pattern"), never claims of maliciousness.
- **Real RAG** — persistent local vector database, not regenerated on startup;
  retrieval returns actual source documents with relevance scores.
- **LLM abstraction** — `ollama`, `openai`, `nvidia` providers via environment
  variables; template-based fallback when no LLM is available.
- **Transparent risk engine** — LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN
  with an explicit list of contributing factors.
- **Intent detection** — 8-class sender intent extraction (credential request,
  money request, download, personal data, prize, confirmation, engagement,
  other) feeding the risk decision.

### v2.1 — Enterprise Integration Layer
- **REST API** (v2) — 13+ endpoints for analysis, history, batch, system, webhooks, plugins.
- **Authentication** — API Keys, JWT, Role-Based Access Control (Admin, Analyst, Developer, ReadOnly, Guest).
- **Batch Analysis API** — CSV, TXT, JSON, ZIP uploads processed asynchronously with job IDs and polling.
- **Webhook System** — event-driven notifications with retries, signing, timeouts, backoff.
- **Plugin Framework** — isolated plugin lifecycle (`initialize`, `shutdown`, `metadata`, `capabilities`, `health`).
- **Event Bus** — internal pub/sub for `MessageReceived`, `AnalysisStored`, `WebhookTriggered`, etc.
- **Official SDKs** — Python, JavaScript, Java with auth, retries, timeouts, error handling.
- **OpenAPI 3.1** auto-generated documentation with Swagger UI and ReDoc.

### v2.2 — Threat Intelligence Platform
- **IOC Extraction Engine** — modular extractors for URLs, domains, IPv4/IPv6, emails, phones, URL shorteners; pluggable registry.
- **Normalization** — scheme lowercasing, trailing-punctuation removal, domain/email canonicalisation, phone digit normalisation.
- **Validation** — syntax, IP, domain, email, phone sanity checks without pure regex.
- **Threat Cache & Persistence** — in-memory + JSON storage, TTL, LRU/TTL eviction, revision tracking, indexed queries, compaction, statistics.
- **Async Threat Lookup Engine** — coordinator, scheduler, dispatcher, executor, retry (exponential backoff + jitter), timeout, concurrency limiter, circuit breaker, metrics.
- **Provider Integrations** — Google Safe Browsing + VirusTotal with configurable API keys, rate-limit awareness, cache-first flow, normalised `ThreatEvidence` output.
- **Reputation Aggregation & Evidence Fusion** — weighted scoring, confidence estimation (5-factor), conflict detection, severity mapping, explainable summaries.
- **Unified Evidence Integration Engine** — evidence registry, evidence graph with full traceability, merger with conflict detection, confidence calculation, human-readable explanations.
- **Threat Intelligence Dashboard** — interactive Jinja2 dashboard with Chart.js visualisation covering threat overview, IOC explorer, evidence timeline, threat graph, provider status, provider comparison, threat heatmap, cache analytics, execution metrics, threat history, and confidence breakdown.

---

## 4. Architecture

```
USER INPUT (SMS / TEXT / EMAIL / raw email)
        │
        ▼
Input normalization & email parsing
        │
        ▼
Preprocessing ──────► URL/email/phone/money extraction
  (TF-IDF features)         │
        │                   ▼
        ▼             URL analysis (static)
ML classifier              │
 (primary decision)        ▼
        │             Indicator engine (rules)
        ▼                   │
Prediction + confidence     │
        ├───────────────────┤
        ▼                   ▼
   Risk engine (LOW/MEDIUM/HIGH/CRITICAL/UNCERTAIN + factors)
        │
        ▼
RAG retrieval ──────────► ChromaDB / fallback store (persistent)
        │
        ▼
Explanation (LLM ── available? ── template fallback)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              v2.2 Threat Intelligence Platform        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  IOC Engine  │→ │  Threat Cache│→ │ Async Lookup │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Providers  │→ │  Aggregation │→ │   Evidence   │ │
│  │ (GSB + VT)   │  │   Engine     │  │   Engine     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│           │                   │                   │    │
│           ▼                   ▼                   ▼    │
│     ┌──────────────────────────────────────────────┐ │
│     │         Threat Intelligence Dashboard         │ │
│     │  (Overview · IOC Explorer · Timeline · Graph) │ │
│     │  (Provider Status · Comparison · Heatmap)     │ │
│     │  (Cache Analytics · Metrics · History)        │ │
│     └──────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
        │
        ▼
Structured JSON  +  SQLite history
        │
        ▼
WEB UI (FastAPI + Jinja2 dashboard)
```

Clear separation of concerns:

- **ML** = spam/ham detection (never influenced by RAG/LLM).
- **RAG** = knowledge retrieval / evidence (adds context, never decides).
- **LLM** = explanation / recommendation (explains the ML verdict).
- **Threat Intelligence** = independent layer sitting between providers and the decision engine, never modifying the core AI pipeline.

---

## 5. Technologies

| Concern | Tool |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| ML | scikit-learn, joblib, pandas |
| NLP features | TF-IDF (word + bigram, sublinear TF) |
| Vector DB | ChromaDB (fallback: dependency-free numpy store) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (fallback: n-gram hashing) |
| LLM | Ollama / any OpenAI-compatible API / NVIDIA NIM (all optional) |
| Storage | SQLite (stdlib `sqlite3`) |
| Threat Intel | ChromaDB (fallback: dependency-free numpy store) |
| Frontend | HTML5, CSS3, Jinja2 templates, Chart.js |
| Testing | pytest |

---

## 6. Project Structure

```
TextShield/
├── app/
│   ├── main.py                  # FastAPI app factory (create_app) + page routes
│   ├── api/                     # REST routers (thin; logic lives in services)
│   │   ├── routes_analysis.py   #   POST /api/analyze
│   │   ├── routes_history.py    #   history list/delete/clear
│   │   ├── routes_stats.py      #   stats + model-info
│   │   ├── routes_system.py     #   health/readiness/version/config/status
│   │   ├── routes_knowledge.py  #   knowledge-base status/rebuild
│   │   ├── routes_ioc.py        #   POST /api/v2/ioc/extract, /validate  (v2.2)
│   │   ├── routes_cache.py      #   GET/DELETE /api/v2/threat/cache        (v2.2)
│   │   ├── routes_aggregation.py#   POST /api/v2/threat/aggregate        (v2.2)
│   │   ├── routes_evidence.py   #   POST/GET /api/v2/evidence             (v2.2)
│   │   ├── routes_dashboard.py  #   GET /api/v2/dashboard/*               (v2.2)
│   │   └── middleware.py        #   request-id + request logging
│   ├── core/                    # settings (env), constants, feature flags,
│   │   │                        # exceptions, error handlers, DI container
│   │   ├── settings.py          #   typed settings from env/.env
│   │   ├── constants.py         #   shared constants
│   │   ├── features.py          #   feature flags
│   │   ├── container.py         #   service registry (dependency injection)
│   │   ├── exceptions.py        #   typed error hierarchy
│   │   ├── errors.py            #   global exception handlers (JSON envelope)
│   │   └── logging.py           #   structured logging + request-id filter
│   ├── threat/                  # v2.2 Threat Intelligence Platform
│   │   ├── ioc/                 # IOC Extraction Engine
│   │   │   ├── models.py        #   IOCType, ExtractedIOC
│   │   │   ├── base.py          #   BaseExtractor interface
│   │   │   ├── registry.py      #   ExtractorRegistry
│   │   │   ├── normalizer.py    #   Normalization rules
│   │   │   ├── validator.py     #   Validation rules
│   │   │   ├── engine.py        #   IOCEngine orchestrator
│   │   │   └── extractors/      #   URL, Domain, IP, Email, Phone, ShortURL
│   │   ├── cache/               # Threat Cache & Persistence Layer
│   │   │   ├── models.py        #   CacheRecord, CacheRevision
│   │   │   ├── storage.py       #   InMemoryStorage + PersistentStorage
│   │   │   ├── manager.py       #   CRUD, TTL, eviction, revisions
│   │   │   ├── repository.py    #   Indexed queries
│   │   │   ├── eviction.py      #   LRU / TTL policies
│   │   │   ├── cleanup.py       #   Expired removal, pruning, compaction
│   │   │   ├── serializer.py    #   JSON export/import
│   │   │   └── statistics.py    #   Hit ratio, provider distribution
│   │   ├── execution/           # Async Threat Lookup Engine
│   │   │   ├── coordinator.py   #   Request lifecycle orchestration
│   │   │   ├── scheduler.py     #   Priority queue scheduling
│   │   │   ├── dispatcher.py    #   Concurrent provider task dispatch
│   │   │   ├── executor.py      #   Concurrency-limited execution
│   │   │   ├── retry.py         #   Exponential backoff with jitter
│   │   │   ├── timeout.py       #   Global / provider timeouts
│   │   │   ├── cancellation.py  #   Graceful cancellation
│   │   │   ├── concurrency.py   #   Semaphore-based concurrency limiter
│   │   │   ├── circuit_breaker.py#  CLOSED/OPEN/HALF-OPEN per provider
│   │   │   ├── health.py        #   Provider execution health
│   │   │   └── metrics.py       #   Requests/s, latency, queue depth
│   │   ├── providers/           # Threat Intelligence Providers
│   │   │   ├── google_safe_browsing/  # GSB client, mapper, validator, config
│   │   │   ├── virustotal/          # VT client, mapper, validator, config
│   │   │   └── threat_indicator.py  #   ThreatIndicator dataclass
│   │   ├── aggregation/         # Reputation Aggregation & Evidence Fusion
│   │   │   ├── models.py        #   ThreatProfile, ThreatSeverity
│   │   │   ├── weighting.py     #   Provider weights + weighted scorer
│   │   │   ├── confidence.py    #   5-factor confidence estimation
│   │   │   ├── conflict.py      #   Conflict detection & summary
│   │   │   ├── fusion.py        #   Evidence fuser → ThreatProfile
│   │   │   └── engine.py        #   AggregationEngine orchestrator
│   │   └── cache.py             # Legacy threat cache (compatibility)
│   ├── evidence/                # v2.2 Unified Evidence Integration Engine
│   │   ├── models.py            #   EvidenceItem, EvidenceSource, EvidenceGraph
│   │   ├── registry.py          #   EvidenceRegistry (pluggable sources)
│   │   ├── validator.py         #   Evidence schema validation
│   │   ├── confidence.py        #   Multi-factor confidence calculation
│   │   ├── merger.py            #   Merge, conflict detection, traceability
│   │   ├── graph.py             #   Adjacency-list graph, provenance chains
│   │   ├── engine.py            #   EvidenceEngine orchestration
│   │   └── explanation.py       #   Human-readable evidence summaries
│   ├── analytics/               # Dashboard & Security Analytics
│   │   ├── dashboards.py        #   Summary, provider status, cache, metrics, confidence
│   │   ├── metrics.py           #   MetricsEngine, MetricsRecord, MetricsSummary
│   │   ├── history.py           #   AnalysisHistory, HistoryService, get_dashboard_history
│   │   ├── statistics.py        #   Confidence/risk/intent/behaviour distributions
│   │   ├── summaries.py         #   Threat score distribution, provider comparison
│   │   ├── config.py            #   Analytics configuration
│   │   ├── reports.py           #   Report generation
│   │   ├── explainability.py    #   Explainability engine
│   │   ├── monitoring.py        #   System monitor & service health
│   │   └── audit.py             #   Audit logger & service
│   ├── database/                # migrations + repositories + V1 facade
│   │   ├── base.py              #   connections + migration runner
│   │   ├── migrations.py        #   versioned schema migrations
│   │   └── repositories/        #   history/analytics/kb/settings/logs access
│   ├── schemas/                 # Pydantic models (analysis/history/analytics/system)
│   ├── services/                # business logic (analysis, history, analytics,
│   │   │                        # configuration, models, system status, KB)
│   │   ├── analysis_service.py  #   pipeline orchestration
│   │   └── risk_engine.py       #   transparent risk scoring
│   ├── ml/                      # ML classifier pipeline
│   │   ├── preprocess.py        # cleaning, unicode normalization, placeholders
│   │   ├── features.py          # TF-IDF builder
│   │   ├── classifier.py        # trained model wrapper (SPAM/HAM + proba)
│   │   ├── indicators.py        # rule-based indicator engine
│   │   ├── intent.py            # sender intent detection
│   │   ├── url_analyzer.py      # static URL pattern analysis
│   │   └── input_detection.py   # raw-mail parsing / type detection
│   ├── rag/                     # RAG pipeline
│   │   ├── embeddings.py        # sentence-transformers / hashing providers
│   │   ├── vector_store.py      # ChromaDB / simple-store backends
│   │   ├── retriever.py         # embed + search + status
│   │   ├── llm.py               # provider abstraction (ollama/openai/nvidia)
│   │   └── generator.py         # explanation + recommendation generation
│   ├── sdk/                     # Official SDKs (Python / JavaScript / Java)
│   ├── utils/                   # file/text/date/validation/response helpers
│   ├── templates/               # Jinja2 pages (including dashboard)
│   └── plugins/                 # Plugin framework
├── frontend/                    # v2.2 Dashboard frontend
│   ├── src/
│   │   ├── pages/
│   │   │   └── ThreatDashboard/
│   │   └── components/
│   │       ├── ThreatSummary/
│   │       ├── IOCExplorer/
│   │       ├── EvidenceTimeline/
│   │       ├── ThreatGraph/
│   │       ├── ProviderStatus/
│   │       ├── ProviderComparison/
│   │       ├── ThreatHeatmap/
│   │       ├── CacheStatistics/
│   │       ├── ExecutionMetrics/
│   │       ├── RecentThreats/
│   │       ├── ThreatHistory/
│   │       └── ConfidenceBreakdown/
├── static/
│   ├── css/style.css
│   ├── js/                      # common.js (shared helpers) + page logic
│   └── images/
├── data/
│   ├── raw/                     # CSV datasets (sample included)
│   ├── processed/               # cleaned + split (auto-generated)
│   └── README.md                # dataset guide
├── knowledge_base/              # RAG corpus (10 categories)
├── models/                      # trained artifacts (auto-generated)
├── vector_db/                   # vector database (auto-generated)
├── scripts/
│   ├── prepare_dataset.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   └── build_knowledge_base.py
├── tests/                       # pytest suite
│   ├── threat/
│   │   ├── ioc/                 # IOC extraction tests
│   │   ├── cache/               # Cache tests
│   │   ├── execution/           # Execution engine tests
│   │   ├── aggregation/         # Aggregation engine tests
│   │   ├── providers/           # Provider tests
│   │   └── dashboard/           # Dashboard analytics tests
│   ├── evidence/                # Evidence integration tests
│   └── rag/                     # RAG pipeline tests
├── docs/                        # Documentation
│   ├── v2.1/                    # Enterprise Integration Layer docs
│   ├── IOC_Extraction.md        # v2.2 IOC Engine docs
│   ├── Threat_Cache.md          # v2.2 Cache docs
│   ├── Threat_Execution.md      # v2.2 Execution engine docs
│   ├── Threat_Aggregation.md    # v2.2 Aggregation docs
│   ├── Unified_Evidence.md      # v2.2 Evidence integration docs
│   ├── Dashboard.md             # v2.2 Dashboard docs
│   └── providers/               # Provider-specific docs
├── requirements.txt
├── pytest.ini
├── run.py
└── README.md                    # This file
```

---

## 7. Installation

```bash
# 1. clone / copy the project folder
cd TextShield

# 2. create a virtual environment
python -m venv .venv

# 3. activate it
#    Windows:      .venv\Scripts\activate
#    macOS/Linux:  source .venv/bin/activate

# 4. install dependencies
pip install -r requirements.txt

# 5. configure (optional) and verify setup
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

> **Optional heavy extras:** `requirements.txt` includes `chromadb` and
> `sentence-transformers` (pulls PyTorch). If you cannot install them, the app
> automatically falls back to a zero-dependency hashing embedder and a numpy
> vector store — everything still works.

---

## 8. Dataset Setup

```bash
python scripts/prepare_dataset.py
```

- Reads **every CSV** in `data/raw/`, auto-detects text/label columns,
  removes empties/duplicates, normalises labels, prints class distribution,
  and writes `train.csv` / `test.csv` (stratified 80/20, deterministic seed).
- A small curated sample (`data/raw/sample_sms_dataset.csv`, 264 rows) is
  included so the project runs immediately.
- For a stronger model, add the **UCI SMS Spam Collection** (`spam.csv`) to
  `data/raw/` — fully documented in `data/README.md`.

---

## 9. Model Training

```bash
python scripts/train_model.py        # compare NB / LR / LinearSVM, save best
python scripts/evaluate_model.py     # report on held-out test set
```

- Training compares **Multinomial Naive Bayes**, **Logistic Regression** and
  **Linear SVM** (calibrated probabilities).
- Selection: best `F1 (spam)` → then `precision (spam)` → then accuracy.
- Artifacts written to `models/`: `spam_classifier.joblib`,
  `tfidf_vectorizer.joblib`, `model_metadata.json`, `evaluation_report.json`
  (and `confusion_matrix.png` if matplotlib is installed).

---

## 10. RAG Knowledge Base

```bash
python scripts/build_knowledge_base.py
```

- Reads all documents under `knowledge_base/`, chunks them (~700 chars,
  overlapping), embeds them and stores vectors in `vector_db/`.
- The vector DB **persists**; it is not rebuilt on app start. Rebuild anytime
  via the script, the dashboard button, or `POST /api/knowledge-base/rebuild`.

---

## 11. LLM Setup (optional)

Copy `.env.example` → `.env` and choose a provider:

| Provider | `.env` |
|---|---|
| Ollama (local, recommended) | `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.1:8b` |
| OpenAI-compatible | `LLM_PROVIDER=openai`, `LLM_MODEL=...`, `LLM_API_KEY=sk-...` |
| NVIDIA NIM | `LLM_PROVIDER=nvidia`, `LLM_MODEL=meta/llama-3.3-70b-instruct`, `LLM_API_KEY=...` |
| None (template explanations) | `LLM_PROVIDER=none` |

API keys are read from the environment only — never commit a real `.env`.
With no LLM configured or reachable, the app automatically uses the
deterministic template explainer and flags `explanation_source: "template"`.

---

## 12. Running the Application

```bash
python run.py
# or
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000**

Quick check: `GET /api/health` returns model/RAG/LLM status.

---

## 13. API Documentation

Interactive docs (Swagger UI) at **http://127.0.0.1:8000/docs**.

### v1 API (original)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analyze` | Analyse a message (SMS/text/email, incl. raw email) |
| GET | `/api/history` | List history (filters, order, pagination) |
| DELETE | `/api/history/{id}` | Delete one history entry |
| DELETE | `/api/history` | Clear all history |
| GET | `/api/stats` | Analytics aggregates |
| GET | `/api/model-info` | Model metadata + metrics + comparison |
| GET | `/api/health` | Service health (model/RAG/LLM) |
| GET | `/api/readiness` | Readiness probe (DB + migrations) |
| GET | `/api/version` | Name / version / environment |
| GET | `/api/config/status` | Effective runtime configuration |
| GET | `/api/status` | App status: uptime, feature flags, readiness |
| GET | `/api/knowledge-base` | RAG build status |
| POST | `/api/knowledge-base/rebuild` | Rebuild vector DB from `knowledge_base/` |

### v2.1 API (Enterprise Integration)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v2/analyze` | Single message analysis |
| POST | `/api/v2/batch` | Batch analysis (CSV/TXT/JSON/ZIP) |
| GET | `/api/v2/history` | Analysis history |
| GET | `/api/v2/system/health` | System health |
| GET | `/api/v2/system/metrics` | System metrics |
| POST | `/api/v2/webhooks` | Register webhook |
| GET | `/api/v2/plugins` | List registered plugins |

### v2.2 API (Threat Intelligence Platform)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v2/ioc/extract` | Extract IOCs from text |
| POST | `/api/v2/ioc/validate` | Validate an IOC |
| GET | `/api/v2/threat/cache` | List cache entries |
| GET | `/api/v2/threat/cache/{ioc}` | Get cache entry |
| DELETE | `/api/v2/threat/cache/{ioc}` | Delete cache entry |
| POST | `/api/v2/threat/cache/refresh` | Refresh cache |
| GET | `/api/v2/threat/cache/statistics` | Cache statistics |
| POST | `/api/v2/threat/aggregate` | Aggregate threat evidence |
| GET | `/api/v2/threat/profile/{ioc}` | Get threat profile |
| POST | `/api/v2/evidence/collect` | Collect evidence from all subsystems |
| GET | `/api/v2/evidence/{analysis_id}` | Get unified evidence |
| GET | `/api/v2/evidence/graph/{analysis_id}` | Get evidence graph |
| GET | `/api/v2/dashboard/summary` | Dashboard summary |
| GET | `/api/v2/dashboard/providers` | Provider status |
| GET | `/api/v2/dashboard/history` | Threat history (paginated) |
| GET | `/api/v2/dashboard/cache` | Cache analytics |
| GET | `/api/v2/dashboard/metrics` | Execution metrics |
| GET | `/api/v2/dashboard/threats` | Recent threats |
| GET | `/api/v2/dashboard/score-distribution` | Score distribution |
| GET | `/api/v2/dashboard/provider-comparison/{ioc}` | Provider comparison |

---

## 14. Threat Intelligence Platform (v2.2)

The Threat Intelligence Platform is a provider-independent layer that sits
between external threat providers and the decision engine. It never modifies
the core AI pipeline.

### Components

- **IOC Extraction Engine** — modular, pluggable extractors for URLs, domains,
  IP addresses (IPv4/IPv6), email addresses, phone numbers, and URL shorteners.
  Each extractor implements `supports()`, `extract()`, `normalize()`, `validate()`.
  New extractors can be added without modifying existing code.

- **Threat Cache & Persistence** — in-memory + JSON storage with TTL-based
  expiration, LRU/TTL eviction policies, revision tracking, indexed queries
  (by IOC type, provider, score, confidence, date), compaction, and
  comprehensive statistics (hit ratio, provider distribution, top queried IOCs).

- **Async Threat Lookup Engine** — a fully asynchronous orchestration engine
  with configurable concurrency limits, priority scheduling, exponential
  backoff with jitter retries, global and per-provider timeouts, graceful
  cancellation, per-provider circuit breakers (CLOSED/OPEN/HALF-OPEN), and
  detailed execution metrics.

- **Provider Integrations** — Google Safe Browsing and VirusTotal providers
  with configurable API keys, rate-limit awareness, cache-first lookup flow,
  and normalised `ThreatEvidence` output that is identical regardless of
  which provider produced it.

- **Reputation Aggregation & Evidence Fusion** — combines evidence from
  multiple providers into a unified `ThreatProfile` using configurable
  provider weights (default: GSB 0.35, VT 0.30, OpenPhish 0.15, PhishTank 0.10,
  URLhaus 0.10), 5-factor confidence estimation, conflict detection, and
  severity mapping (Informational → Low → Medium → High → Critical).

- **Unified Evidence Integration Engine** — collects evidence from every
  subsystem (Threat Intelligence, Hybrid ML, LLM Reasoning, RAG Retrieval,
  Rule Engine, Semantic Analysis, Intent Analysis) into a single
  `EvidenceGraph` with full traceability. The evidence graph preserves the
  chain from raw message through every processing stage to the final
  unified evidence item.

### Design Principles

- **Provider-independent** — the engine works with any future provider without modification.
- **Thread-safe** — all managers use `RLock` for concurrent access.
- **Scalable** — configurable concurrency limits, connection pooling, horizontal scalability support.
- **Extensible** — new evidence sources, extractors, and providers register through the registry without modifying existing code.
- **Persistent** — JSON-based persistence layer for cache data.

---

## 15. Threat Intelligence Dashboard (v2.2)

The Threat Intelligence Dashboard provides an enterprise-grade visualisation
of every stage of the threat intelligence workflow.

### Dashboard Sections

1. **Threat Overview** — total analyses, threat score distribution, high-risk detections, average confidence, provider health
2. **IOC Explorer** — search by URL, domain, email, phone, IP, hash; view history, threat profile, provider results, evidence, timeline
3. **Evidence Timeline** — visualises the full chain: message → IOC extraction → cache lookup → provider response → aggregation → evidence integration → decision
4. **Threat Graph** — interactive graph showing relationships between messages, indicators, providers, evidence, and threat profiles
5. **Provider Status** — health, latency, success rate, failures, quota usage, circuit breaker state
6. **Provider Comparison** — compare provider responses for the same IOC, highlighting agreement, disagreement, missing responses, confidence
7. **Threat Heatmap** — threat volume, severity distribution, confidence distribution, provider coverage
8. **Cache Analytics** — cache size, hit/miss ratio, TTL distribution, evictions, top queried IOCs
9. **Execution Metrics** — average lookup time, concurrency, queue depth, retries, timeouts, requests per second
10. **Threat History** — searchable, filterable history (date, IOC type, threat score, provider, severity) with pagination
11. **Confidence Breakdown** — breakdown of confidence contributions from each subsystem

### Visualisation

Charts are rendered with **Chart.js** loaded from CDN. Each chart component
is lazy-loaded: bar charts for distributions, line charts for timelines,
doughnut charts for breakdowns, and heatmaps for temporal volume.

### UX

- **Responsive** — works on desktop and mobile browsers.
- **Dark mode compatible** — CSS variables support theme switching.
- **Explainable** — every data point includes a human-readable explanation of
  which subsystem produced it, when, why, and supporting artifacts.
- **Accessible** — semantic HTML with ARIA labels.

---

## 16. Screenshots

*Placeholder — add screenshots of the dashboard, result cards, history,
analytics and knowledge-base pages here.*

```
📸 dashboard.png    📸 result-spam.png    📸 result-ham.png
📸 history.png      📸 analytics.png      📸 knowledge-base.png
📸 threat-dashboard.png  📸 provider-status.png  📸 evidence-graph.png
```

---

## 17. ML Evaluation (bundled sample dataset)

On the held-out test split of the included sample dataset (53 rows):

| Algorithm | Accuracy | Precision (spam) | Recall (spam) | F1 (spam) |
|---|---|---|---|---|
| Multinomial Naive Bayes | 0.943 | 1.000 | 0.812 | 0.897 |
| Logistic Regression | 0.849 | 1.000 | 0.500 | 0.667 |
| **Linear SVM (selected)** | **0.962** | **0.938** | **0.938** | **0.938** |

Confusion matrix (selected model, ham rows/spam rows):

```
             HAM    SPAM
HAM          36      1
SPAM          1     15
```

- Measured with `python scripts/train_model.py` / `scripts/evaluate_model.py`.
- Full numbers are always available under *About → Trained model* in the app
  and in `models/model_metadata.json`.

---

## 18. Limitations

- **Informational only** — risk verdicts are heuristic scores, not legal,
  financial or security assurance.
- **Static URL analysis** — TextShield never fetches URLs; a URL with no
  pattern warnings is *not* guaranteed safe.
- **Model quality follows data** — the bundled sample dataset is small; adding
  the UCI SMS Spam Collection (see `data/README.md`) considerably improves
  generalization. The three-model comparison is repeated automatically on the
  next `train_model.py` run.
- **LLM quality varies** — generated explanations depend on the configured
  model; the deterministic template always works and is always available as a
  baseline.
- **Language scope** — the indicator engine and sample dataset are English /
  Indian-English (₹, KYC, UPI, Aadhaar); other languages need dataset + rule
  extensions.
- **Hashing-embedding fallback** — semantic quality is lower than
  sentence-transformers; install `sentence-transformers` for best retrieval.

---

## 19. Future Scope

- Stream-based background classification (email inbox scanner, SMS inbox).
- Multilingual support (additional datasets + rule sets).
- Transformer classifier (fine-tuned BERT) as an alternative primary model.
- Additional threat intelligence providers (OpenPhish, PhishTank, URLhaus, AbuseIPDB).
- Threat aggregation / timeline views.
- Decision Engine integration.
- Full SPA frontend (React/Vue) with WebSocket-based real-time updates.
- Containerization (Docker) and deployment guides.
- Rate limiting + authentication for deployed instances.
- Knowledge base expansion with user feedback loop (human-in-the-loop labels → periodic retraining).

---

## 20. Security Considerations

- No secrets in source: all keys come from `.env` (git-ignored).
- User input is sanitized, validated and length-limited (Pydantic).
- The URL analyzer performs **no network requests** and never executes links.
- The knowledge-base rebuild touches only files under `knowledge_base/`.
- The LLM is used only to explain; the ML verdict drives classification.
- History stores only a SHA-256 hash of message content by default
  (`HISTORY_STORE_PREVIEW=false`); preview storing is opt-in and deletable.
- Logging excludes API keys, passwords and message bodies.
- The threat intelligence platform never logs API keys or exposes provider credentials.
- All external responses are validated and sanitised before storage.

---

## 21. Running the Tests

```bash
python -m pytest
```

The test suite covers: preprocessing, spam/ham prediction, indicator detection,
URL analysis, risk calculation, RAG retrieval, settings, repositories, services,
lifecycle, all API endpoints, IOC extraction, threat cache, async execution engine,
reputation aggregation, evidence integration, provider integrations, and the
dashboard analytics — with 90%+ coverage targets per module.

---

## 22. Documentation

Detailed write-ups live in `docs/`:

### Core
- [`docs/architecture.md`](docs/architecture.md) — system design & data flow
- [`docs/ml_pipeline.md`](docs/ml_pipeline.md) — preprocessing, features, training, evaluation
- [`docs/rag_pipeline.md`](docs/rag_pipeline.md) — knowledge base, embeddings, retrieval, generation
- [`docs/api.md`](docs/api.md) — full API reference with examples
- [`docs/setup.md`](docs/setup.md) — environment & troubleshooting

### v2.1 — Enterprise Integration Layer
- [`docs/v2.1/`](docs/v2.1/) — API spec, auth guide, roadmap

### v2.2 — Threat Intelligence Platform
- [`docs/IOC_Extraction.md`](docs/IOC_Extraction.md) — IOC Extraction Engine architecture, rules, examples, extension guide
- [`docs/Threat_Cache.md`](docs/Threat_Cache.md) — cache architecture, lifecycle, storage, revision model, TTL strategy, configuration
- [`docs/Threat_Execution.md`](docs/Threat_Execution.md) — execution architecture, lifecycle, scheduler, coordinator, dispatcher, retry policy, circuit breaker design, performance characteristics, configuration, examples
- [`docs/Threat_Aggregation.md`](docs/Threat_Aggregation.md) — aggregation architecture, scoring model, confidence calculation, conflict resolution, examples
- [`docs/Unified_Evidence.md`](docs/Unified_Evidence.md) — evidence architecture, evidence graph design, integration guide, extension guide, examples
- [`docs/Dashboard.md`](docs/Dashboard.md) — dashboard architecture, components, analytics, configuration, examples
- [`docs/providers/`](docs/providers/) — provider-specific documentation (Google Safe Browsing, VirusTotal, OpenPhish, PhishTank, URLhaus, AbuseIPDB)

---

## 23. Project Overview (v2.2.0)

TextShield v2.2 is a production-hardened, open-source spam/phishing detection platform with explainable AI and a full Threat Intelligence Platform. See `docs/architecture.md` + `docs/production/Architecture_Review.md` for diagrams.

## 24. Quick Start

```bash
git clone https://github.com/DEBEYENDU/TextShield.git && cd TextShield
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python scripts/prepare_dataset.py
python scripts/train_model.py
python scripts/build_knowledge_base.py
python run.py  # http://127.0.0.1:8000  docs at /docs
```

Docker (if provided): `docker compose up --build`

## 25. Configuration

All via `app/core/settings.py` + `.env` / `*_FILE` secrets. Key vars: `APP_ENV`, `DATABASE_URL`, `MAX_MESSAGE_LENGTH`, `RAG_TOP_K`, `LLM_PROVIDER/MODEL/BASE_URL/API_KEY`, `API_KEY`, `ALLOWED_ORIGINS`, `FEATURE_*`, risk thresholds. Startup `Settings.validate()` fails fast. See `docs/setup.md` + `.env.example`.

## 26. REST API

Base `http://127.0.0.1:8000`; OpenAPI `/docs`. See Section 13 + `docs/api.md`. Key groups: `/api/analyze`, `/api/history`, `/api/v2/*`, `/api/v2/threat/*`, `/api/v2/dashboard/*`, `/api/system/*`. Consistent envelope `{status,data,error}`, pagination `skip/limit` or `page/page_size`, 413/429 handling, `/api/health` → `/readiness`/`/liveness`/`/healthz`.

## 27. SDKs

Official `app/sdk/` Python / JS / Java clients with auth, retries, timeout, error handling. See `examples/`:

```python
from examples.python_client import TextShieldClient
c = TextShieldClient(base_url="http://127.0.0.1:8000", api_key="...")
print(c.analyze("You've won! http://bit.ly/abc"))
```

## 28. Threat Intelligence (v2.2)

See Section 14 + `docs/providers/` + `docs/IOC_Extraction.md` etc. Six providers (GSB, VT, OpenPhish, PhishTank, URLhaus, AbuseIPDB) via `IThreatProvider`, cache-first, retry/rate-limit/circuit-breaker, normalized `ThreatEvidence`.

## 29. RAG

ChromaDB + `sentence-transformers` (fallback hashing). Corpus `knowledge_base/` 10 categories, chunk 700 chars overlap, persistent `vector_db/`, `RAG_TOP_K=4`. See `docs/rag_pipeline.md` + `docs/Knowledge_Base_Design.md`.

## 30. Hybrid ML

TF-IDF (word+bigram, sublinear) + Linear SVM (calibrated) primary (selected via F1 spam). Fallbacks NB/LR. See `docs/ml_pipeline.md`.

## 31. Decision Engine

`app/decision/decision_engine.py` fuses ML confidence + rule indicators + RAG evidence + risk engine (LOW/MEDIUM/HIGH/CRITICAL/UNCERTAIN) transparent factors. Deterministic, LLM never overrides.

## 32. Evidence Engine

`app/evidence/engine.py` + `app/threat/aggregation` + `EvidenceGraph` (see Section 14 unified engine) traceability chain message → IOC → cache → providers → aggregation → evidence → decision. See `docs/Unified_Evidence.md`.

## 33. Screenshots

Already in Section 16 + `frontend/` demo; placeholder pending real captures in release.

## 34. Project Structure

See Section 6 canonical tree (includes `app/threat/`, `app/evidence/`, `frontend/`, `benchmarks/`, `examples/`).

## 35. Roadmap

- v2.3 planned: Postgres, PWA/service-worker, mTLS, transformer classifier, multilingual rules, streaming inbox scanner. See `docs/Implementation_Roadmap.md` + `docs/production/Production_Readiness_Checklist.md`.

## 36. Contributing

PRs welcome! Branch `v2.2-dev` → `main`. Run `scripts/lint.sh`, `black`, `ruff`, `mypy`, `pytest -q --cov`, `benchmarks/suite.py`. See commit conventions in Section 23 Git Workflow. Issues at https://github.com/DEBEYENDU/TextShield/issues.

## 37. License

MIT — see `LICENSE` (to be added if missing; default MIT as per `pyproject.toml`). Enterprise evaluation permitted, no warranty.

## 38. Citation

```bibtex
@software{textshield2026,
  title={TextShield: AI-powered spam & ham detection with RAG and threat intelligence},
  author={Karmakar, Debeyendu Nirmal},
  year={2026},
  version={2.2.0},
  url={https://github.com/DEBEYENDU/TextShield}
}
```

## 39. Acknowledgements

Supervisor: NA, B.E. Computer Engineering; libraries: scikit-learn, FastAPI, ChromaDB, sentence-transformers, Chart.js; providers Abuse.ch, PhishTank, OpenPhish.

## 40. Known Limitations

- Sample dataset small; UCI SMS improves generalization; English/Indian-English rules.
- Heuristic URL analysis never fetches URLs.
- Hashing fallback lower semantic quality.
- SQLite WAL single-instance (migrate to Postgres for scale).
- See `docs/production/Known_Issues.md` + Section 18.

## 41. Future Work

Stream scanner, multilingual, BERT classifier, additional providers, SPA+WebSockets, Docker, rate-limit+auth hardening, KB human-in-the-loop. See Section 19 + `docs/production/Known_Issues.md`.

---

## 23. Git Workflow

The project uses feature branches:

```
v2.2-dev          — Development branch for v2.2 threat intelligence platform
v2.1-dev          — Development branch for v2.1 enterprise integration layer
main              — Stable release branch
```

Commit messages follow the conventional format:
```
feat(api): add v2 analysis endpoint
feat(auth): implement JWT middleware
feat(ioc): implement extraction engine
feat(cache): implement cache manager
feat(execution): implement coordinator
feat(aggregation): implement weighting model
feat(evidence): implement evidence registry
feat(dashboard): add threat overview
docs(ioc): document extraction engine
test(ioc): add comprehensive tests
```

All tests must pass before every commit.

---

## Authors

**TextShield** — Academic project.

- Author: Debeyendu Nirmal Karmakar
- Course / Institution: B. E (Computer Engineering)
- Supervisor: NA

Built with Python, scikit-learn, FastAPI, ChromaDB and open-source LLM tooling.