# Semantic Understanding Engine

Phase 5 of the TextShield V2.0 roadmap: a self-contained module that converts
raw messages (SMS, email, chat, plain text) into a structured *semantic
representation* — detected language, domains, topics, entities, semantic
features, embeddings and confidence scores — for later consumption by the
intent analysis, decision engine, RAG and explainability phases.

**Scope boundary:** the engine **never classifies** (no spam probability, no
risk score) and has **zero dependencies** on RAG, LLM reasoning or the
Decision Engine. It is a deterministic, reusable foundation. It is exposed as
an internal service via the DI container only; there is no API endpoint yet.

---

## Architecture

```
app/semantic/
├── __init__.py            package docstring (scope contract)
├── semantic_models.py     output schema (Pydantic), domain/topic vocab
├── semantic_utils.py      preprocessing primitives (pure functions)
├── embedding_service.py   configurable embedding provider + LRU cache
├── semantic_pipeline.py   extraction pipeline (contexts/topics/entities/…)
└── semantic_service.py    facade + similarity utilities (public entry)
```

### Data flow

```
raw message ──► semantic_utils (normalize, parse input kind)
             ──► language detection (script heuristic)
             ──► sentence segmentation
             ──► context detection (12 domains + confidence)
             ──► topic extraction (13 topics + confidence)
             ──► entity extraction (13 types + confidence)
             ──► feature computation (length/emojis/requests/…)
             ──► embeddings (message, sentences, subject, body)
             ──► SemanticAnalysisResult
```

### Similarity service

`app/semantic/semantic_service.py` also provides:

- `cosine_similarity(vec_a, vec_b)` — cosine in `[0, 1]` (0 for empty vectors)
- `embedding_distance(vec_a, vec_b)` — Euclidean distance
- `sentence_similarity(text_a, text_b)` — cosine over embeddings with a
  token-overlap (Jaccard) fallback

---

## Pipeline stages

### 1. Preprocessing (`semantic_utils.py`)

| Stage | What it does |
| --- | --- |
| `normalize_unicode` | NFC + confusable folding (e.g. curly quotes → ASCII) |
| `normalize_special_characters` | fold smart punctuation |
| `clean_whitespace` | collapse runs of whitespace |
| `preprocess_text` | canonical pipeline of the three above |
| `extract_emojis` | keep emoji list (never stripped) |
| `parse_raw_email` | stdlib `email` parser → `{subject, sender, body}` |
| `parse_sms` / `decompose_email` | input-kind helpers |
| `segment_sentences` | sentence boundary split with abbreviation guard |
| `detect_language` | script-range heuristic → `(label, confidence)` |

Supported language scripts: English, Hindi, Bengali, Tamil, Telugu, Marathi,
Arabic, Russian, Chinese, Japanese, Korean, Greek, Hebrew, Thai.

### 2. Context detection (`semantic_pipeline.py`)

Keyword lexicons over 12 domains: `banking`, `finance`, `shopping`,
`education`, `employment`, `government`, `healthcare`, `technology`,
`personal_communication`, `business`, `social_media`, `unknown`.
Top-4 domains are returned with confidence
`clamp(0.45 + 0.12 · hits/best_hits)`. Empty/gibberish input degrades to
`unknown` with confidence `0.8`.

### 3. Topic extraction

13 topics: Payment, Prize, Investment, Loan, Delivery, Verification, Account,
Promotion, Meeting, Education, Support, Travel, Communication — same
confidence model as contexts. Empty input yields `[]`.

### 4. Entity extraction

Structured entities with `type`, `value`, `normalized`, `confidence`,
`start`/`end` spans and optional `attributes`:

- `email`, `url`, `phone`, `money` (`Rs.5000`, `INR 500`, `$10` …)
- `date` (ISO, d/m/y, `15 Dec`, `Dec 15`, `25 Dec 2026`), `time`
- `account_number`, `tracking_number` (UPS `1Z…`, FedEx 12-digit)
- `organization` / `bank` / `company` (case-sensitive suffix + word lists)
- `person` (honorifics, greetings), `location` (suffixes + 38-city gazetteer)

Overlapping patterns are de-duplicated (e.g. phone numbers that are digit
substrings of account/tracking/date codes are dropped).

### 5. Semantic features

`SemanticFeatures` records message length, word/sentence/question/imperative
counts, emoji/url/email/phone/money/date/time counts, and boolean flags for
requests, offers, urgency, financial references, credential requests and
personal-information requests. **Note:** these are semantic descriptors, not
spam indicators — interpretation belongs to later phases.

### 6. Embeddings (`embedding_service.py`)

- Configurable Sentence-Transformers model (default `all-MiniLM-L6-v2`,
  384-dim); device auto-detected (`SEMANTIC_DEVICE=cpu|cuda|gpu|mps|auto`).
- Embeddings are produced for the **message**, each **sentence**, the email
  **subject** and email **body**.
- LRU cache (default 512 entries) keyed by normalized text; `batch_size`
  batching; `clear_cache()` / `cache_info()`.
- Deterministic `_HashingEmbedder` fallback (n-gram hashing into 384-dim)
  guarantees the engine works even without the model or torch.
- `embedding_provider` in the result reports which backend was used.

### 7. Confidence

`SemanticConfidence{language, context, topic, entity}` — estimated from the
same data the engine extracted. There is deliberately **no spam/risk
confidence** in this module.

---

## Inputs / Outputs

### Inputs (`SemanticService.analyze_message`)

| Parameter | Type | Notes |
| --- | --- | --- |
| `message` | `str` | primary text (sms/chat/text) |
| `message_type` | `str` | `text` \| `sms` \| `email` \| `chat` |
| `subject`, `sender`, `body` | `str?` | structured email fields |
| `email_raw` | `str?` | raw pasted email (parsed automatically) |
| `include_embeddings` | `bool` | default `True`; disable for throughput |

Typed helpers: `analyze_sms`, `analyze_email`, `analyze_text`,
`analyze_chat`, `batch_analyze(messages)`.

### Output (`SemanticAnalysisResult`)

```python
{
  "language": "en",
  "contexts": [{"domain": "banking", "confidence": 0.57}],
  "topics": [{"topic": "Account", "confidence": 0.57}],
  "entities": [{"type": "money", "value": "Rs.5000", "confidence": 0.93}],
  "embedding_dimension": 384,
  "embeddings": {"message": [...], "sentences": [[...]], "subject": [...], "body": [...]},
  "semantic_features": {"message_length": 166, "sentence_count": 4, ...},
  "confidence": {"language": 0.95, "context": 0.57, "topic": 0.57, "entity": 0.93},
  "embedding_provider": "sentence_transformers",
  "engine_version": "1.0.0",
  "message_preview": "Your bank account will be blocked. ..."
}
```

Empty or malformed input never raises: it yields a valid result with
`language="unknown"`, `contexts=[{domain="unknown"}]`, empty topics/entities
and a zero vector embedding.

---

## Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `SEMANTIC_ENABLED` | `true` | master switch |
| `SEMANTIC_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformers model |
| `SEMANTIC_EMBEDDING_DIMENSION` | `384` | fallback embedder dimension |
| `SEMANTIC_CACHE_SIZE` | `512` | embedding LRU cache entries |
| `SEMANTIC_BATCH_SIZE` | `16` | batch size for embedding calls |
| `SEMANTIC_DEVICE` | `auto` | `cpu` \| `cuda` \| `gpu` \| `mps` \| `auto` |
| `SEMANTIC_LANGUAGE_DETECTION` | `auto` | reserved for future models |

---

## DI integration

The service is registered as `semantic` in `app/core/container.py`
(`create_container` → `semantic_service`), making it available to route
dependencies via `get_request_registry(request).get("semantic")`. It is an
**internal interface only** — no HTTP endpoint is exposed in this phase.

---

## Limitations

- Keyword-based contexts/topics/entities are English-first; multilingual
  detection covers script, not meaning.
- Language detection is a script heuristic with a fixed confidence of `0.95`
  — not a full language model.
- Entity extraction is regex-based; unusual formats (e.g. `₹` variants,
  non-Latin numerals) are only partially covered.
- The Sentence-Transformers model downloads on first use; offline systems
  transparently fall back to the hashing embedder.
- No intent classification, no risk scoring and no explanation generation —
  by design; those are later phases.
