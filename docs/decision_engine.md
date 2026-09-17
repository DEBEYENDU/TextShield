# TextShield v4.0 — Adaptive Decision & Evidence Fusion (RFC-007)

Twelve evidence sources fuse into one policy-gated verdict, with weights
adapted per message category. No static weights, no hardcoded thresholds —
everything lives in `config/decision_policies.json`.

## Architecture

```text
analysis ─▶ extract 12 source votes (p_spam, confidence, evidence)
  │
  ├─▶ adaptive weights = policy base × category profile × reliability
  │                        (floor 0.4 keeps sources audible,
  │                         cap 1.8 + share cap stop dominance)
  ├─▶ conviction weighting (strong evidence speaks louder)
  ├─▶ capped-share fusion → P(spam) + per-source contributions
  ├─▶ corroborated override (overruling ML needs 2 convicted sources)
  ├─▶ calibrated confidence (agreement × coverage → empirical map)
  ├─▶ policy gate (thresholds per conservative/balanced/…)
  ├─▶ review routing (conflict, confidence, risk, novelty, boundary…)
  └─▶ structured explanation (risk, reasons, confidence, contributors)
```

## Evidence sources

ML, RAG, knowledge graph, threat intel, behavior, intent, message type,
entities, LLM reasoning, multi-agent consensus, historical similarity,
legitimacy. Sources abstain when they have nothing to say (template LLM
output, `other` intents, calm behavior); ML and legitimacy anchor every
decision. Key lesson learned: absence of threat is not evidence of
safety — benign votes must come from positive trust signals.

## Policies

| Policy | Spam thr. | Character |
|---|---|---|
| conservative | 0.35 | catches everything (FN 0), reviews ~everything |
| balanced | 0.50 | default (acc 0.944, FP 4, FN 1) |
| aggressive | 0.65 | minimal FPs (FP 1, FN 13) |
| enterprise | 0.50 | balanced + forced review on conflict/Medium+ |
| research | 0.50 | generous routing for labeling |
| custom | — | balanced + JSON overrides |

Select via `DECISION_POLICY` env var or `get_policy(name, overrides={...})`.

## Review routing

Routes on convicted-evidence conflict in toss-ups, sub-threshold
confidence, high-risk uncertainty, model/evidence disagreement > 0.4,
high-threat unknown types, unknown domains, novel patterns, and
low-confidence boundary cases. Queue persists in the evaluation
feedback store (`needs_review`), so resolutions become training evidence.

## Confidence model

`0.6 × agreement + 0.4 × coverage`, mapped through an isotonic
calibrator learned from evaluation runs (static fallback). Uncertainty
= 1 − calibrated confidence.

## Configuration

All thresholds, base weights, category profiles and fusion caps live in
`config/decision_policies.json`. No code change needed to retune.

## API

`POST /api/decision|/evidence|/confidence|/review`,
`GET /api/review`, `POST /api/review/{id}/claim|resolve`,
`GET /api/decision/policies`. The analysis payload also carries
`adaptive_decision` (additive; legacy fields untouched).
