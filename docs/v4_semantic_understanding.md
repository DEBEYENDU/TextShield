# TextShield v4.0 — Semantic Understanding Pipeline (RFC-001)

The system understands **WHAT a message is** before deciding whether it is
malicious. The binary Spam/Ham classifier is untouched and remains the
backward-compatible prediction authority.

## Pipeline order

```text
Incoming Message
  -> Language Detection          (app/understanding/language.py)
  -> Message Type Classification (app/understanding/message_type.py, 21 types)
  -> Intent Detection            (app/understanding/intent_detector.py, 16 intents)
  -> Entity Extraction           (app/understanding/entities.py, 17 groups)
  -> Threat Indicators           (app/understanding/threat.py, 19 families)
  -> Legitimacy Indicators       (app/understanding/legitimacy.py, 17 signals)
  -> Evidence Summary            (app/understanding/evidence.py — no verdict)
  -> Message Profile             (app/understanding/profile.py)
  -> Current Spam Classifier     (app/ml/classifier.py — unchanged)
  -> RAG -> LLM -> Decision Engine (all unchanged)
```

## Module contract

Every stage returns `{label, confidence, evidence/reasoning}` and never
raises: the orchestrator (`app/understanding/pipeline.py`) degrades each
stage independently, so understanding can never break analysis.

## Scoring philosophy

No single-keyword rules. Every classifier combines weighted semantic
phrases, structural signals (sender, greeting/closing, layout) and the
semantic context engine, with confidence derived from the best-vs-runner-up
margin. Two explicit false-positive guards live in the threat engine:

- `toll free` never counts as promotional language;
- `as per <authority> order` citations never count as authority abuse.

## Message profile

```text
Category: Educational Announcement | Intent: Congratulate
Threat Score: 0.08 | Trust Score: 0.91 | Entities: 6 | URLs: 0
Credential Requests: 0 | Urgency: No | Payment Request: No
Overall Context: Institutional communication.
```

Risk bands: `<0.15` Very Low, `<0.35` Low, `<0.60` Medium, `<0.80` High,
else Critical.

## Consuming the API

`POST /api/analyze` now also returns `understanding` (full stage output)
and `message_profile` (the profile above). All pre-existing fields are
byte-identical; the v1 `response_model` additionally exposes the two new
optional fields.

## Performance

Regex/semantic scoring only — no model loads. Measured worst-case
**~5 ms** per message against a 300 ms budget.

## Extending

- New message type: add phrases to `_TYPE_PHRASES` + context boost mapping.
- New intent: add phrases to `_INTENT_PHRASES`.
- New entity group: extend `grouped` in `entities.py` (+ regex).
- New threat family: append to `_EXTRA_PATTERNS` in `threat.py`.
- New trust signal: append to `_TRUST_PATTERNS` in `legitimacy.py`.
- Benchmark: add cases to `data/understanding_benchmark.json`; they are
  asserted automatically by `tests/test_understanding.py`.
