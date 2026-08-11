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
FastAPI application (app/main.py)
 ├── /api/analyze ......... routes_analysis
 ├── /api/history ......... routes_history
 ├── /api/stats ........... routes_stats
 ├── /api/model-info ...... routes_stats
 ├── /api/health .......... routes_health
 ├── /api/knowledge-base .. routes_health
 └── pages / • • /about ... Jinja2 + static
      │
      ├── services/analysis_service.py   (orchestrator)
      │     ├── ml/classifier.py         (joblib model + TF-IDF)
      │     ├── ml/indicators.py         (rule engine)
      │     ├── ml/url_analyzer.py       (static URL checks)
      │     ├── services/risk_engine.py  (score → LOW/MEDIUM/HIGH)
      │     ├── rag/retriever.py         (embed + search)
      │     └── rag/generator.py         (LLM or template explainer)
      ├── database/ (SQLite)             (history + stats)
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
   ├── URLs    : analyze_urls(raw text)        → [{url, warnings, flags}]
   └── (email) : analyze_domain(sender domain) → merged into urls/indicators
   ▼
Risk engine: base score by class → indicator weights → URL flags
             → confidence adjustment → RAG family bonus → level
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
| `core/config.py` | Environment settings, path resolution | n/a |
| `ml/preprocess.py` | Cleaning + placeholder masking for URLs/emails/phones/money | n/a |
| `ml/features.py` | TF-IDF vectorizer builder | n/a |
| `ml/classifier.py` | Loads joblib model; `predict()` → label + probability | `RuntimeError` → 503 via service |
| `ml/indicators.py` | 15+ regex/lexical rule groups; structured evidence | never fails |
| `ml/url_analyzer.py` | Static URL pattern analysis; cautious wording | never fails; no network |
| `rag/embeddings.py` | sentence-transformers or hashing provider | falls back to hashing |
| `rag/vector_store.py` | ChromaDB or numpy store; persistent on disk | falls back to simple store |
| `rag/retriever.py` | Embed query, top-k retrieval, status | returns [] on failure |
| `rag/generator.py` | LLM (JSON) explanation; template fallback | template always works |
| `rag/llm.py` | ollama / openai / nvidia clients; env-only keys | `None` → template mode |
| `services/risk_engine.py` | 0–100 score with explicit factors | never fails |
| `services/analysis_service.py` | Orchestrates pipeline; history insert | history failure never breaks analysis |
| `database/database.py` | SQLite schema + queries (hash-based privacy) | isolated |
| `schemas/analysis.py` | Pydantic validation, length limits | 422 on invalid input |
| `api/*` | HTTP layer, error mapping | 404/422/500/503 |

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