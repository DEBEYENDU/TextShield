# Intent & Behavior Analysis Engine

Phase 6 of the TextShield V2.0 roadmap: a reusable engine that converts the
Semantic Understanding Engine's structured output into a *behavioral
profile* — what the sender is trying to achieve, what the recipient is
expected to do, which behavioral characteristics and manipulation techniques
are present, how urgent the message is, which trust signals it uses, and the
overall communication style and goal.

It sits directly after the Semantic Understanding Engine and will later feed
the Evidence Validator, Decision Engine, Explainability Engine and Risk
Assessment Engine.

**Scope boundary:** the engine **describes** intent and behavior; it NEVER
determines whether a message is spam, phishing or malicious, and it assigns
no risk score. It depends only on the semantic module (no RAG, no vector DB,
no LLM, no ML classifier).

---

## Architecture

```
app/intent/
├── __init__.py              package docstring
├── models.py                output schema + vocabularies + DetectorStrategy
├── utils.py                 AnalysisContext builder, scoring primitives
├── intent_service.py        sender intent detection (26 intents)
├── action_service.py        requested-action detection (16 actions)
├── behavior_service.py      behavior analysis (15 behaviors)
├── manipulation_service.py  psychological manipulation (16 techniques)
├── context_service.py       urgency, trust signals, style, goal
└── pipeline.py              orchestration + aggregation (public entry)
```

### Data flow

```
SemanticAnalysisResult (or raw message → semantic pipeline)
        │
        ▼
AnalysisContext   (normalized text, sentences, tokens, entities,
                   topics, domains, semantic features, language)
        │
        ├─► IntentService        → intents[]      (confidence + evidence)
        ├─► ActionService        → requested_actions[]
        ├─► BehaviorService      → behaviors[]
        ├─► ManipulationService  → manipulation[]
        ├─► ContextService       → urgency, trust_signals, style, goal
        ▼
IntentAnalysisResult  (aggregated, per-category confidence)
```

The pipeline never re-implements preprocessing: `build_context()` reuses
`SemanticPipeline` when no pre-computed `SemanticAnalysisResult` is supplied
(with embeddings disabled for throughput), or consumes the caller's existing
result directly.

### Strategy contract

Every service implements the `DetectorStrategy` interface
(`name` + `detect(ctx)`). Rule-based detectors are the default; a future ML
or LLM-based detector can replace any service by implementing the same
contract and injecting it into `IntentPipeline` — no other code changes.

---

## Detectors

### 1. Sender intents (`intent_service.py`)

26 intents: Inform, Notify, Advertise, Promote, Sell, Request Payment,
Request Credentials, Request OTP, Request Personal Information, Request
Verification, Request Contact, Request Download, Request Installation,
Request Account Update, Offer Reward, Offer Discount, Offer Job, Threaten,
Warn, Create Curiosity, Create Urgency, Social Conversation, Business
Communication, Education, Support, Unknown.

Multiple intents may coexist (capped by `INTENT_MAX_INTENTS`, default 4,
ordered by confidence). If nothing crosses the confidence threshold, the
result contains a single `Unknown` intent (low confidence is never hidden).

**Not keyword-only:** each intent combines marker hits with *structural
gates* drawn from semantic features — e.g. `Request OTP` only fires on
request phrases ("reply with your OTP"), not on the bare word "otp", so a
bank's "Your OTP is 483920. Do not share it" is detected as Notify/Warn,
not as a request; `Request Payment` requires a financial reference or
requestive structure; `Call Number`/`Request Contact` require a phone or
email entity.

### 2. Requested actions (`action_service.py`)

16 actions: Click Link, Reply, Call Number, Open Attachment, Visit Website,
Download File, Install Application, Transfer Money, Verify Identity, Provide
OTP, Provide Password, Provide Banking Information, Provide Personal
Information, Purchase Product, Ignore, No Action. Gated on semantic entities
(e.g. `Click Link` requires a URL entity, `Call Number` requires a phone).

### 3. Behaviors (`behavior_service.py`)

15 descriptive behaviors: Financial Request, Credential Request,
Authentication Request, Identity Verification, External Redirection,
Information Collection, Conversation Continuation, Marketing, Advertisement,
Promotion, Appointment, Reminder, Support Conversation, Customer Service,
Personal Discussion. Behaviors are never labeled good/bad.

### 4. Psychological manipulation (`manipulation_service.py`)

16 techniques: Urgency, Fear, Reward, Greed, Authority, Scarcity, Curiosity,
Trust, Familiarity, Friendliness, Pressure, Social Obligation, Reciprocity,
Guilt, Hope, Excitement. Each returns technique, confidence and supporting
evidence snippets (matched phrases from the message).

### 5. Urgency (`context_service.py`)

Continuous 0–100 score → level: `none | low | medium | high | critical`.
Scoring combines urgency language, pressure/threat language, exclamation
marks and ALL-CAPS ratio (the latter two only count when real urgency
language exists, so a friendly "Hi!" never inflates urgency). Evidence
snippets are returned for transparency.

### 6. Trust signals (`context_service.py`)

Official language, Brand references, Government references, Bank
references, Professional tone, Formal formatting, Personal greetings —
with confidence and evidence. These are *indicators of trust-building
techniques*, recognized without judging legitimacy.

### 7. Conversation style

Formal, Informal, Marketing, Customer Support, Educational, Transactional,
Personal, Corporate, Promotional, Unknown — scored independently, argmax
with deterministic tie-break priority, `Unknown` when all scores are low.

### 8. Communication goal

Share Information, Collect Information, Complete Transaction, Obtain
Credentials, Drive Website Traffic, Build Trust, Create Fear, Offer
Opportunity, Continue Conversation — derived from detected intents,
behaviors, manipulation and trust signals (never from raw keywords alone).

---

## Inputs / Outputs

### Input (`IntentPipeline.analyze`)

| Parameter | Type | Notes |
| --- | --- | --- |
| `message` | `str` | primary text |
| `message_type` | `str` | `text` \| `sms` \| `email` \| `chat` |
| `subject`, `sender`, `body`, `email_raw` | `str?` | email inputs |
| `semantic_result` | `SemanticAnalysisResult?` | reuse a prior semantic pass |
| `intent_threshold` / `behavior_threshold` / `urgency_threshold` / `max_intents` | override config per call |

### Output (`IntentAnalysisResult`)

```python
{
  "intents": [{"name": "Request Payment", "confidence": 0.42, "evidence": ["pay", "account 1234..."]}],
  "requested_actions": [{"name": "Transfer Money", "confidence": 0.43, "evidence": [...]}],
  "behaviors": [{"name": "Financial Request", "confidence": 0.43, "evidence": [...]}],
  "manipulation": [{"name": "Urgency", "confidence": 0.37, "evidence": ["immediately"]}],
  "urgency": {"level": "medium", "score": 29.2, "confidence": 0.46, "evidence": ["immediately"]},
  "trust_signals": [{"name": "Bank references", "confidence": 0.42, "evidence": [...]}],
  "conversation_style": {"style": "Transactional", "confidence": 0.37, "evidence": [...]},
  "communication_goal": {"goal": "Complete Transaction", "confidence": 0.39, "evidence": [...]},
  "confidence": {"intents": 0.40, "requested_actions": 0.43, "behaviors": 0.43,
                 "manipulation": 0.37, "urgency": 0.46, "trust_signals": 0.42,
                 "conversation_style": 0.37, "communication_goal": 0.39},
  "language": "en",
  "engine_version": "1.0.0",
  "message_preview": "Your bank account will be blocked..."
}
```

Empty or malformed input never raises: `Unknown` intent, `No Action`,
empty behaviors/manipulation, `none` urgency, `Unknown` style,
`Share Information` goal.

---

## Decision philosophy

- **Descriptive, never judgmental.** The engine reports intent, behavior
  and techniques; interpretation (risk, spam, action) belongs to later
  phases.
- **Deterministic.** The same input always yields the same profile — every
  detector is a pure function of `AnalysisContext`.
- **Evidence-backed.** Every detection carries the phrases that triggered
  it, so downstream explainability can quote the message directly.
- **Low confidence is not hidden.** Sub-threshold predictions are either
  dropped only after the configurable threshold, and when nothing crosses,
  `Unknown`/`No Action`/`none` are returned explicitly.
- **Structural gates over keywords.** Detectors combine markers with
  entities, topics, features and requestive structure (see examples in the
  detector sections), and a strategy interface allows model replacement.

## Confidence estimation

Per-item confidence: `base + boost · (hits / pattern_count)`, clamped to
`[0, 1]`, plus feature-based boosts (urgency language, entities present,
emoji/exclamation counts, requestive ratio). Category confidence in
`result.confidence` is the mean of the category's detected items; urgency
uses its own level confidence; style and goal use their model confidence.
All values are deterministic and rounded to 4 decimals.

---

## Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `INTENT_ENABLED` | `true` | master switch |
| `INTENT_CONFIDENCE_THRESHOLD` | `0.35` | minimum confidence for intents/actions |
| `INTENT_BEHAVIOR_THRESHOLD` | `0.30` | minimum confidence for behaviors/manipulation/trust |
| `INTENT_URGENCY_THRESHOLD` | `0.30` | floor for reporting an urgency level |
| `INTENT_MAX_INTENTS` | `4` | maximum number of reported intents |

Thresholds can also be overridden per call via `analyze(..., intent_threshold=...)`.

---

## DI integration

Registered as `intent` in `app/core/container.py` (`create_container` →
`intent_pipeline`), available via
`get_request_registry(request).get("intent")`. Internal interface only —
no HTTP endpoint in this phase.

---

## Limitations

- Rule-based detectors are English-first; other languages are analyzed via
  the semantic engine's script detection, but lexicon coverage is English.
- Intent/action vocabulary is fixed by the tuples in `models.py`; custom
  vocabularies are not configurable yet.
- Sarcasm, implied requests and very short one-word messages often fall to
  `Unknown`/`No Action` (by design — the engine prefers honest low
  confidence over guessing).
- The engine does not track conversation history; each message is analyzed
  in isolation.
- No classification, risk or legitimacy judgment — by design.
