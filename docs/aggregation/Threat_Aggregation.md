# Threat Aggregation & Evidence Fusion Engine

## Architecture
- `models.py`: `ThreatSeverity` enum, `ThreatProfile` dataclass
- `weighting.py`: `ProviderWeights` dataclass, `WeightedScorer`
- `confidence.py`: `ConfidenceCalculator` (agreement, quality, freshness, reliability, stability)
- `conflict.py`: `ConflictDetector` (disagreement, low-confidence, outdated evidence)
- `fusion.py`: `EvidenceFuser` – orchestrates scoring → confidence → conflict → `ThreatProfile`
- `engine.py`: `AggregationEngine` – public API `aggregate()` / `aggregate_from_indicators()`

## ThreatProfile Schema
| Field | Type | Description |
|---|---|---|
| `overall_threat_score` | float | Composite threat score 0.0‑1.0 |
| `confidence` | float | Aggregated confidence 0.0‑1.0 |
| `severity` | `ThreatSeverity` | `INFORMATIONAL` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `provider_agreement` | float | Ratio of providers in agreement (0.0‑1.0) |
| `supporting_evidence` | list | Evidence dicts supporting the conclusion |
| `conflicting_evidence` | list | Evidence dicts contradicting the conclusion |
| `evidence_count` | int | Total number of evidence items considered |
| `reliability_score` | float | Average provider reliability 0.0‑1.0 |
| `reasoning_summary` | str | Human‑readable explanation |
| `timestamp` | datetime | When the profile was computed |

## Scoring Model
- **WeightedScorer** applies per‑provider weights (default: GSB 0.35, VT 0.30, OpenPhish 0.15, PhishTank 0.10, URLhaus 0.10).
- Each evidence item contributes `weight * base * confidence` where `base = 1` for malicious, `0` for benign.
- Final score = weighted sum / total weight, normalised to 0.0‑1.0.

## Confidence Estimation
`ConfidenceCalculator.calculate()` blends five factors:
1. **Agreement ratio** – proportion of providers reporting malicious.
2. **Average confidence** – mean of provider confidence values.
3. **Provider reliability** – weighted by each provider's historical accuracy.
4. **Freshness** – exponential decay over 24 h half‑life since last update.
5. **Stability** – 1.0 if all providers agree, 0.5 otherwise.
Result is a float in [0.0, 1.0], rounded to 4 dp.

## Conflict Resolution
`ConflictDetector.detect()` returns a dict with:
- `has_disagreement` – True if some providers say malicious and some benign.
- `disagreement_ratio` – proportion of the minority opinion.
- `conflicting_reputations` – list of `{status, count}`.
- `low_confidence_providers` – entries with confidence < 0.5.
- `outdated_evidence` – items beyond the configurable TTL.
- `conflict_score` – weighted sum (disagreement 0.5 + low‑conf 0.3 + outdated 0.2), bounded to 0‑1.

## API
- **POST** `/api/v2/threat/aggregate` – body: `{evidences: [...], provider_names?: [...], provider_reliability?: {...}, provider_timestamps?: {...}}`
  - Returns a `ThreatProfile` JSON object.
- **GET** `/api/v2/threat/profile/{ioc_value}` – (future) returns a stored profile for the IOC; currently returns a not‑found placeholder.

## Configuration
- Provider weights are set via `ProviderWeights` (defaults as above) and can be overridden at engine construction or through the `set_weight()` method.
- Confidence and severity thresholds are tunable per deployment.

## Examples
```python
engine = AggregationEngine()
evidences = [
    {"provider": "google_safe_browsing", "threat_status": "malicious", "confidence": 0.8},
    {"provider": "virustotal",           "threat_status": "malicious", "confidence": 0.9},
    {"provider": "openphish",            "threat_status": "benign",    "confidence": 0.4},
]
profile = engine.aggregate(evidences)
# profile.overall_threat_score ≈ 0.69
# profile.confidence ≈ 0.68
# profile.severity == ThreatSeverity.HIGH
# profile.provider_agreement ≈ 0.67
# profile.reasoning_summary contains "provider disagreement detected"
```

## Known Limitations
- Heuristic‑based confidence/conflict formulas; production deployment should calibrate weights/thresholds on real provider data.
- No integration with the Decision Engine (per RFC‑007 stop condition).
- Only five confidence factors are currently modelled; additional signals (e.g., temporal trends) can be added.

## Remaining RFC Dependencies
- Decision Engine integration (excluded by design).
- Additional threat intelligence providers beyond GSB + VT.
- Dashboard or UI components.
- Front‑end changes.