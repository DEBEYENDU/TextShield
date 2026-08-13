# TextShield — System Architecture

This document describes the overall design of TextShield, the data flow
through the analysis pipeline, and the responsibilities of each module.

## 1. Design goals

1. **The ML model is the primary classifier.** RAG and LLM layers may enrich
   or explain the result — they never change the SPAM/HAM decision.
2. **Graceful degradation.** Missing model → clear 503. Missing vector DB →
   analysis continues without evidence. Missing LLM → template explanations.
3. **Transparency.** Every verdict is accompanied by evidence: indicators,
   URL findings, retrieved knowledge, and a list of risk factors.
4. **Runnable on a student laptop.** Local, open-source components; no paid
   API required for the core application.

## 2. Runtime topology

```
Browser (dashboard)
      │  HTTP / JSON
      ▼
FastAPI application (app/main.py — create_app factory)
 ├── /api/analyze .......... routes_analysis
 ├── /api/history .......... routes_history
 ├── /api/stats ............ routes_stats
 ├── /api/model-info ....... routes_stats
 ├── /api/health, /api/readiness, /api/version,
 │   /api/config/status, /api/status ... routes_system
 ├── /api/knowledge-base (+ /rebuild) .. routes_knowledge
 └── pages / • /about ... Jinja2 + static
      │  (request-id & logging middleware; global error handlers)
      ├── services/analysis_service.py   (orchestrator)
      │     ├── ml/classifier.py         (joblib model + TF-IDF)
      │     ├── ml/indicators.py         (rule engine)
      │     ├── ml/intent.py             (sender intent extraction)
      │     ├── ml/url_analyzer.py       (static URL checks)
      │     ├── services/risk_engine.py  (score → LOW/MEDIUM/HIGH/CRITICAL/UNCERTAIN)
      │     ├── rag/retriever.py         (embed + search)
      │     └── rag/generator.py         (LLM or template explainer)
      ├── database/ (migrations + repositories, SQLite)
      └── rag/llm.py                     (provider abstraction)
```

## 3. Analysis pipeline (data flow)

```
User input
   │  input_type: sms | text | email   (+ optional raw email header parsing)
   ▼
normalize + combine subject/sender/body
   ▼
[parallel branches]
   ├── ML path : normalize_text → TF-IDF transform → predict_proba → SPAM/HAM + p
   ├── Rules   : detect_indicators(raw text)   → [{indicator, severity, evidence}]
   ├── Intent  : detect_intent(raw text)       → {label, description, evidence}
   ├── URLs    : analyze_urls(raw text)        → [{url, warnings, flags}]
   └── (email) : analyze_domain(sender domain) → merged into urls/indicators
   ▼
Risk engine: base score by class → indicator weights → intent signal → URL flags
             → confidence adjustment → RAG family bonus → level
             (CRITICAL requires malicious intent + corroboration; UNCERTAIN
              when the model is guessing with no supporting evidence)
   ▼
RAG: embed(message) → query vector store → top-k hits (source/category/score)
   ▼
Generator: build structured prompt → LLM (JSON) | template fallback
   ▼
Response JSON + SQLite history insert (hash of content, not content)
```

## 4. Module responsibilities

| Module | Responsibility | Failure behavior |
|---|---|---|
| `core/settings.py` | Typed settings from env/.env; path resolution | n/a |
| `core/constants.py` | Shared constants (risk levels, intents, defaults) | n/a |
| `core/features.py` | Feature flags (rag/llm/history/evidence/analytics) | disabled stage skips |
| `core/container.py` | Service registry (DI); routes depend on registry | startup error if missing |
| `core/exceptions.py` | Typed error hierarchy → HTTP mapping | global handlers |
| `core/errors.py` | Centralized exception handlers (consistent envelope) | always responds JSON |
| `api/middleware.py` | Request-id + request logging | never blocks requests |
| `ml/preprocess.py` | Unicode normalization + cleaning + placeholders | n/a |
| `ml/features.py` | TF-IDF vectorizer builder | n/a |
| `ml/classifier.py` | Loads joblib model; `predict()` → label + probability | `RuntimeError` → 503 via service |
| `ml/indicators.py` | 15+ regex/lexical rule groups; structured evidence | never fails |
| `ml/intent.py` | 8-class sender intent extraction (credential/money/download/personal/prize/confirmation/engagement/other) | never fails |
| `ml/url_analyzer.py` | Static URL pattern analysis; cautious wording | never fails; no network |
| `rag/embeddings.py` | sentence-transformers or hashing provider | falls back to hashing |
| `rag/vector_store.py` | ChromaDB or numpy store; persistent on disk | falls back to simple store |
| `rag/retriever.py` | Embed query, top-k retrieval, status | returns [] on failure |
| `rag/generator.py` | LLM (JSON) explanation; template fallback | template always works |
| `rag/llm.py` | ollama / openai / nvidia clients; env-only keys | `None` → template mode |
| `services/risk_engine.py` | 0–100 score with explicit factors | never fails |
| `services/analysis_service.py` | Orchestrates pipeline; history insert | history failure never breaks analysis |
| `services/history_service.py` | History list/filter/delete/clear (paged) | isolated |
| `services/analytics_service.py` | Dashboard statistics | isolated |
| `services/configuration_service.py` | Effective config + feature-flag snapshot | n/a |
| `services/models_service.py` | Model availability + metadata | returns `available: False` |
| `services/system_status_service.py` | Health/readiness/uptime/status | degraded response |
| `services/kb_service.py` | Knowledge-base status and rebuild | `KnowledgeBaseError` → 500 envelope |
| `database/migrations.py` | Versioned schema changes (append-only) | applied in order, transactional |
| `database/base.py` | Connections + migration runner + `init_db` | locked, rollback on error |
| `database/repositories/*` | Per-aggregate SQL access (history, analytics, kb_metadata, settings, logs) | isolated |
| `schemas/*` | Pydantic validation, length limits | 422 on invalid input |
| `api/*` | Thin HTTP layer via service registry | 404/422/500/503 envelopes |

## 5. Failure handling matrix

| Condition | Behavior |
|---|---|
| Model files missing | `POST /api/analyze` → 503 with setup hint; `/api/health` → `degraded` |
| Vector DB missing/empty | analysis continues; `rag_evidence: []`; UI shows notice |
| Embedding/LLM package missing | automatic fallback providers; no crash |
| LLM unreachable / bad JSON | template explanation, `explanation_source: "template"` |
| Empty or too-long input | 422 via Pydantic (limits from `MAX_MESSAGE_LENGTH`) |
| Malformed raw email | parsed defensively; text used as body |
| DB write failure | logged; analysis response unaffected |

## 6. Privacy & security posture

- Message content is hashed (SHA-256) for history by default.
- LLM prompts receive truncated message excerpts (≤1200 chars) without sender
  identities; keys never logged; no chain-of-thought exposed.
- URL analysis is purely static — no requests to arbitrary hosts.
- Secrets only via environment variables; `.env` git-ignored.