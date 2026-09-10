# TextShield v4.0 — Behavioral Analysis & Social Engineering Engine (RFC-004)

Detects HOW a message attempts to influence the recipient. Another evidence
provider: it never replaces existing components and never classifies.

## Architecture

```text
message (+type/sender) ─▶ BehavioralAnalyzer
  ├─ psychology    18 techniques (authority bias … time constraints)
  ├─ authority     15 personas (CEO fraud … marketplace seller)
  ├─ urgency       semantic score 0..1 + evidence + confidence
  ├─ emotion       12 emotions, persuasion-weighted (not sentiment)
  ├─ persuasion    9 techniques (reward … false reassurance)
  ├─ manipulation  fused score 0..1 + level + narrative
  ├─ linguistic    complexity, readability, tone, grammar, abuse signals
  ├─ conversation  greeting→demand flow, imperatives, CTAs, pressure
  └─ style/profile 13 styles + RFC-004 behavior profile
```

## Scoring philosophy

Weighted semantic phrases plus structural signals (imperative density,
sender context, message-type agreement); confidence from signal strength.
Two calibration guards keep false positives down:

- informational validity windows ("Valid for 10 mins") are discounted;
- polite softeners ("Please arrive early") count as pressure only with a
  demand marker (OTP, pay, verify, …).

## Behavior profile

```json
{
  "communication_style": "Manipulative",
  "psychological_triggers": ["Fear", "Urgency"],
  "social_engineering": ["CEO Fraud"],
  "emotion_profile": {"Fear": 1.0, "Pressure": 0.8},
  "urgency": {"score": 0.9, "level": "Critical"},
  "persuasion": ["Threat", "Authority Reference"],
  "overall_behavior": "Coercive manipulative communication with heavy pressure tactics.",
  "confidence": 0.94
}
```

## Integration points

| Consumer | Mechanism |
|---|---|
| Trust/Threat | `trust_adjustment`/`threat_adjustment` (±0.3 bounded; calm messages earn +trust, coercion adds +threat) reported in `result["behavior"]` |
| RAG | `rag_terms` (e.g. `CEO fraud`, `credential harvesting`) appended to graph expansion retrieval |
| Knowledge graph | `graph_edges` (`CEO Fraud —Uses→ Authority Bias`, technique —TARGETS→ recipient) merged into the Cytoscape payload |
| LLM | BEHAVIORAL ANALYSIS section in the generator prompt |
| API | `result["behavior"]` + `result["behavior_profile"]` (additive; legacy fields untouched) |

## Extending

- New technique/persona: add phrases to the module lexicon + `_RAG_TERMS` entry.
- New emotion/style: extend the taxonomy in `app/behavior/__init__.py` and the scorer.
- Benchmark: add cases to `data/behavior_benchmark.json` (asserted automatically).
