# TextShield — RAG Pipeline

## 1. What RAG does here

RAG (**R**etrieval-**A**ugmented **G**eneration) feeds the explanation layer
with *evidence*: knowledge-base chunks semantically similar to the message
being analyzed. Two honest rules govern the design:

1. RAG **never classifies** — the ML verdict is the verdict.
2. Retrieval results are **never fabricated** — every hit is a real chunk
   stored during the build step, with its source file, category and score.

## 2. Components

```
knowledge_base/ (markdown corpora, 10 categories)
        │  scripts/build_knowledge_base.py
        ▼
chunk + embed (sentence-transformers all-MiniLM-L6-v2 | hashing fallback)
        ▼
vector_db/ (ChromaDB PersistentClient | numpy fallback)
        ▲
        │  app/rag/retriever.py
        │
  message ──embed──► query ──► top-k hits ──► RAG evidence
```

## 3. Knowledge base (`knowledge_base/`)

Categories and example sources:

| Category dir | Example documents |
|---|---|
| `spam_patterns/` | overview, promotional language, urgency tactics, URL tactics, social engineering |
| `phishing/` | phishing overview, credential phishing, brand impersonation |
| `sms_scams/` | sms overview, lottery/prize, delivery, OTP fraud |
| `email_scams/` | email overview, invoice fraud, account verification |
| `banking_scams/` | banking overview, account-blocked, fake payments |
| `job_scams/` | job overview, work-from-home |
| `investment_scams/` | investment overview, crypto scams |
| `loan_scams/` | loan scam overview |
| `examples/` | labeled spam + ham example messages |
| `safety_guidelines/` | self-protection, incident response, safe URL checking |

The content is educational, compiled for the project, and clearly phrased as
pattern documentation (not legal/financial authority).

## 4. Build step (`scripts/build_knowledge_base.py`)

1. Recursively read `*.md` / `*.txt` under `knowledge_base/`.
2. Strip markdown noise, collapse whitespace.
3. Chunk with **CHUNK_SIZE=700** chars, **overlap=100**, splitting on
   sentence boundaries where possible.
4. Embed all chunks with the active embedding provider.
5. `delete_all()` and re-insert (rebuild semantics), persist a
   `structure.json` with build time, counts, categories, provider, backend.

**The vector DB persists.** The app never rebuilds it on startup; rebuilds
happen only via the script, the dashboard button, or
`POST /api/knowledge-base/rebuild`.

## 5. Embedding providers (`app/rag/embeddings.py`)

| Provider | When | Notes |
|---|---|---|
| `sentence_transformers` | default | `all-MiniLM-L6-v2`, 384-dim, CPU-friendly (~90 MB) |
| `hashing` | automatic fallback | deterministic char n-grams (2–4) hashed into a 768-dim L2-normalized vector |

Selection via `EMBEDDING_PROVIDER`. Consistency is guaranteed: the same
provider (and, for transformers, the same model) used at build time is used
at query time, so vector dimensions always match.

## 6. Vector store backends (`app/rag/vector_store.py`)

| Backend | When | Persistence |
|---|---|---|
| `chromadb` | primary | `PersistentClient` at `vector_db/`, cosine space, collection `textshield_knowledge` |
| `simple` | fallback when chromadb is missing | `vectors.npy` + JSON metadata + ids |

Both implement the same interface: `add / query / count / delete_all /
save_structure`, so retrieval logic is backend-agnostic.

## 7. Retrieval (`app/rag/retriever.py`)

```python
hits = retriever.retrieve(message, top_k=settings.RAG_TOP_K)
# → [{document, source, category, chunk_id, score, is_example}, ...]
```

- `score` is cosine similarity (Chroma reports distance → converted to
  `1 - distance`).
- `source` and `document` come from what was stored at build time — no
  fabrication.
- If no knowledge base has been built, `retriever.is_ready == False` and the
  analysis continues with `rag_evidence: []` plus a status note.

## 8. Generation (`app/rag/generator.py`)

`generate_explanation(analysis_dict)`:

1. If an LLM client is configured → build the structured prompt
   (message excerpt, ML verdict + confidence, indicators, URL findings, RAG
   hits, risk level) and ask for **JSON only** (`summary`, `explanation`,
   `recommended_action`). The system prompt forbids overriding the verdict
   and forbids chain-of-thought.
2. Parse JSON; if unusable → **template fallback**.
3. Template mode (`template_explanation`) composes a deterministic
   evidence-grounded explanation and a recommendation chosen by category
   (credentials → "never share OTP/PIN"; payment → "do not send money"; …).

`explanation_source` tells the UI whether the text came from the LLM or the
template, keeping the system honest about its behavior.

## 9. LLM providers (`app/rag/llm.py`)

| Provider | Transport |
|---|---|
| `ollama` | `POST {base}/api/generate` (no key) |
| `openai` | OpenAI-compatible `POST {base}/chat/completions` + Bearer key |
| `nvidia` | same as openai, base `https://integrate.api.nvidia.com/v1` |
| `none` / unset | LLM disabled → template mode |

All credentials come from environment variables; invalid config simply
disables the LLM (logged at WARNING).

## 10. Failure modes

| Scenario | Result |
|---|---|
| sentence-transformers missing | hashing embedder; retrieval still works |
| chromadb missing | numpy store; retrieval still works |
| KB not built yet | `is_ready=False`; analysis without evidence |
| LLM down / bad JSON / no key | template explanation, flagged in response |
| embedding model download offline (first run) | hashing provider covers it |