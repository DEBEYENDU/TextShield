# RFC-007 Implementation Report — Adaptive Decision & Evidence Fusion (v4.0)

**Branch:** `v2.2-dev` | **Status:** All acceptance criteria satisfied

## Architecture

New adaptive layer beside the existing static decision framework
(untouched except one pre-existing `IndentationError` that blocked the
whole package import): `config/decision_policies.json` + `policy.py`
(6 policies), `weighting_adaptive.py` (category × reliability weights,
share caps), `adaptive_engine.py` (12-source extraction, conviction
fusion, corroborated override), `confidence.py` (agreement × coverage),
`calibration.py` (isotonic bins from eval runs + fallback + ECE),
`routing.py` (7 review triggers), `review.py` (queue over the feedback
store), `explanation.py` (RFC-007 shape). Wired additively into
`analysis_service` (`adaptive_decision` key, `DECISION_POLICY` env) and
exposed via 8 endpoints in `routes_decision.py`.

## Adaptive weighting strategy

Policy base × category profile × reliability, floored and capped; shares
re-capped so no source exceeds 35%; conviction (`|p−0.5| × confidence`)
lets strong evidence speak louder. Category examples: Recruitment boosts
agents/legitimacy/graph and attenuates raw threat; Bank Notification
boosts threat intel/ML/entities; Government boosts graph/legitimacy.

## Policy examples (90-sample eval set)

| Policy | Acc | FP | FN | Review |
|---|---|---|---|---|
| balanced | **0.944** | 4 | 1 | 43% |
| conservative | 0.822 | 16 | 0 | 98% |
| aggressive | 0.844 | 1 | 13 | 42% |
| enterprise | 0.944 | 4 | 1 | 99% |

ML baseline: 0.878 / FP 10 / FN 1.

## Benchmark improvements

Decision accuracy **0.878 → 0.944** (+6.6 pts), false positives
**10 → 4** (−60%), false negatives held at 1. All 5 residual errors sit
at p 0.50–0.61 — the boundary zone the review router covers. Calibration
via isotonic mapping; per-source contributions recorded for every
verdict; share sums verified to 1.0 in tests.

## API usage

`POST /api/decision {"message": "..."}` → decision, p_spam,
confidence, risk, policy, category, evidence summary, review routing.
Companion endpoints for evidence, confidence, review queue
(list/claim/resolve) and policy listing. `POST /api/analyze` unchanged.

## Test results

17 tests green; full suite **583 passed**, 0 regressions. Coverage:
policy loading/switching/custom, per-category weight adaptation, share
caps, campus/phish verdicts, source independence, agreement math,
calibrator learning, routing triggers, review lifecycle, explanation
shape, all endpoints, benchmark gates (acc ≥ 0.85, FP ≤ ML, FN ≤ 3,
conservative/aggressive characters), legacy endpoint regression.

## Future enhancements

Learned category profiles from eval feedback; per-source reliability
tracking over time; threshold auto-tuning against FP/FN budgets;
multi-policy shadow mode with drift comparison; review-capacity-aware
routing (priority × analyst bandwidth).
