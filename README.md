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

## 1. Problem statement

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

## 2. Project objectives

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
- Provide a modern responsive dashboard: analyze, history, analytics,
  knowledge base, model information.
- Expose a validated REST API with graceful degradation and logging.
- Be fully runnable on a student laptop, with zero required paid services.

---

## 3. Features

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
- **Transparent risk engine** — LOW / MEDIUM / HIGH with an explicit list of
  contributing factors.
- **History in SQLite** — message content stored as SHA-256 only by default;
  filtering, sorting, pagination, delete.
- **Analytics dashboard** — totals, spam %, risk and type distributions,
  per-day trend; dependency-free canvas charts.
- **Model info page** — algorithm, training date, dataset sizes, metrics and
  the full three-model comparison.
- **Automated tests** — 73 tests covering preprocessing, classification,
  indicators, URLs, risk, RAG and the API.
- **Logging** — rotating file + console; never logs keys or message content.

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
   Risk engine (LOW/MEDIUM/HIGH + factors)
        │
        ▼
RAG retrieval ──────────► ChromaDB / fallback store (persistent)
        │
        ▼
Explanation (LLM ── available? ── template fallback)
        │
        ▼
Structured JSON  +  SQLite history
        │
        ▼
WEB UI (FastAPI + vanilla JS dashboard)
```

Clear separation of concerns:

- **ML** = spam/ham detection (never influenced by RAG/LLM).
- **RAG** = knowledge retrieval / evidence (adds context, never decides).
- **LLM** = explanation / recommendation (explains the ML verdict).

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
| Frontend | HTML5, CSS3, vanilla JavaScript (no external CDNs) |
| Testing | pytest |

---

## 6. Project structure

```
TextShield/
├── app/
│   ├── main.py                  # FastAPI app + page routes
│   ├── api/                     # REST routers
│   │   ├── routes_analysis.py   #   POST /api/analyze
│   │   ├── routes_history.py    #   history list/delete/clear
│   │   ├── routes_stats.py      #   stats + model-info
│   │   └── routes_health.py     #   health + knowledge-base status/rebuild
│   ├── core/                    # config (.env) + logging
│   ├── ml/
│   │   ├── preprocess.py        # cleaning, placeholders, extraction
│   │   ├── features.py          # TF-IDF builder
│   │   ├── classifier.py        # trained model wrapper (SPAM/HAM + proba)
│   │   ├── indicators.py        # rule-based indicator engine
│   │   ├── url_analyzer.py      # static URL pattern analysis
│   │   └── input_detection.py   # raw-mail parsing / type detection
│   ├── rag/
│   │   ├── embeddings.py        # sentence-transformers / hashing providers
│   │   ├── vector_store.py      # ChromaDB / simple-store backends
│   │   ├── retriever.py         # embed + search + status
│   │   ├── llm.py               # provider abstraction (ollama/openai/nvidia)
│   │   └── generator.py         # explanation + recommendation generation
│   ├── database/                # SQLite schema + queries
│   ├── schemas/                 # Pydantic request/response models
│   ├── services/
│   │   ├── analysis_service.py  # pipeline orchestration
│   │   └── risk_engine.py       # transparent risk scoring
│   └── templates/               # Jinja2 pages
├── static/
│   ├── css/style.css
│   ├── js/                      # page logic + canvas charts
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
├── tests/                       # pytest suite (73 tests)
├── docs/                        # architecture, ml_pipeline, rag_pipeline,
│                                # api, setup
├── .env.example
├── requirements.txt
├── pytest.ini
└── run.py
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

## 8. Dataset setup

```bash
python scripts/prepare_dataset.py
```

- Reads **every CSV** in `data/raw/`, auto-detects text/label columns,
  removes empties/duplicates, normalizes labels, prints class distribution,
  and writes `train.csv` / `test.csv` (stratified 80/20, deterministic seed).
- A small curated sample (`data/raw/sample_sms_dataset.csv`, 264 rows) is
  included so the project runs immediately.
- For a stronger model, add the **UCI SMS Spam Collection** (`spam.csv`) to
  `data/raw/` — fully documented in `data/README.md`.

## 9. Model training and evaluation

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

## 10. RAG knowledge-base creation

```bash
python scripts/build_knowledge_base.py
```

- Reads all documents under `knowledge_base/`, chunks them (~700 chars,
  overlapping), embeds them and stores vectors in `vector_db/`.
- The vector DB **persists**; it is not rebuilt on app start. Rebuild anytime
  via the script, the dashboard button, or `POST /api/knowledge-base/rebuild`.

## 11. LLM setup (optional)

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

## 12. Running the application

```bash
python run.py
# or
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000**

Quick check: `GET /api/health` returns model/RAG/LLM status.

## 13. API documentation

Interactive docs (Swagger UI) at **http://127.0.0.1:8000/docs**.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analyze` | Analyze a message (SMS/text/email, incl. raw email) |
| GET | `/api/history` | List history (filters, order, pagination) |
| DELETE | `/api/history/{id}` | Delete one history entry |
| DELETE | `/api/history` | Clear all history |
| GET | `/api/stats` | Analytics aggregates |
| GET | `/api/model-info` | Model metadata + metrics + comparison |
| GET | `/api/health` | Service health (model/RAG/LLM) |
| GET | `/api/knowledge-base` | RAG build status |
| POST | `/api/knowledge-base/rebuild` | Rebuild vector DB from `knowledge_base/` |

Example request:

```json
POST /api/analyze
{
  "input_type": "sms",
  "message": "Congratulations! You have won Rs.50,000. Click here to claim."
}
```

Example response (abridged):

```json
{
  "classification": "SPAM",
  "confidence": 0.988,
  "risk_level": "HIGH",
  "message_type": "sms",
  "indicators": [
    {"indicator": "Prize / lottery claim", "severity": "high",
     "evidence": "you have won", "category": "prize"}
  ],
  "urls": [],
  "rag_evidence": [
    {"document": "Lottery and prize scams...", "source": "lottery_prize_scam.md",
     "category": "sms_scams", "score": 0.62, "is_example": false}
  ],
  "explanation": "This message was classified as SPAM ... matches patterns
                  characteristic of lottery and prize scams ...",
  "explanation_source": "template",
  "recommended_action": "Do not click any links ... Report the message ...",
  "risk_factors": ["ML classified the message as SPAM (confidence 99%)",
                   "Indicator 'Prize / lottery claim' (high)", ...]
}
```

## 14. Screenshots

*Placeholder — add screenshots of the dashboard, result cards, history,
analytics and knowledge-base pages here.*

```
📸 dashboard.png    📸 result-spam.png    📸 result-ham.png
📸 history.png      📸 analytics.png      📸 knowledge-base.png
```

## 15. ML evaluation (bundled sample dataset)

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

## 16. Limitations

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

## 17. Future scope

- Stream-based background classification (email inbox scanner, SMS inbox).
- Multilingual support (additional datasets + rule sets).
- Transformer classifier (fine-tuned BERT) as an alternative primary model.
- Threat-intel integration (Safe Browsing API) for live URL reputation checks.
- User feedback loop (human-in-the-loop labels → periodic retraining).
- Containerization (Docker) and deployment guides.
- Rate limiting + authentication for deployed instances.

## 18. Security considerations

- No secrets in source: all keys come from `.env` (git-ignored).
- User input is sanitized, validated and length-limited (Pydantic).
- The URL analyzer performs **no network requests** and never executes links.
- The knowledge-base rebuild touches only files under `knowledge_base/`.
- The LLM is used only to explain; the ML verdict drives classification.
- History stores only a SHA-256 hash of message content by default
  (`HISTORY_STORE_PREVIEW=false`); preview storing is opt-in and deletable.
- Logging excludes API keys, passwords and message bodies.

## 19. Run the tests

```bash
python -m pytest
```

73 tests covering: preprocessing, spam/ham prediction, indicator detection,
URL analysis, risk calculation, RAG retrieval and all API endpoints.

## 20. Documentation

Detailed write-ups live in `docs/`:

- [`docs/architecture.md`](docs/architecture.md) — system design & data flow
- [`docs/ml_pipeline.md`](docs/ml_pipeline.md) — preprocessing, features, training, evaluation
- [`docs/rag_pipeline.md`](docs/rag_pipeline.md) — knowledge base, embeddings, retrieval, generation
- [`docs/api.md`](docs/api.md) — full API reference with examples
- [`docs/setup.md`](docs/setup.md) — environment & troubleshooting

---

## Authors

**TextShield** — Academic project.

- Author: *(your name here)*
- Course / Institution: *(your course & institution here)*
- Supervisor: *(optional)*

Built with Python, scikit-learn, FastAPI, ChromaDB and open-source LLM tooling.