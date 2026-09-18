# Intelligence Candidate Prioritization

## Purpose
Deterministic, explainable prioritization of research candidates. Priority indicates research value/urgency, NOT threat risk or maliciousness.

## Architecture
`app/intelligence/prioritization.py`

Input: `ResearchCandidate`
Output: `CandidatePriority`
- candidate_id
- priority_score 0.0-1.0
- priority_level LOW/MEDIUM/HIGH/CRITICAL
- factors
- explanation
- confidence
- evidence_summary
- generated_at

## Factors
- evidence_gap: low evidence_count increases priority
- uncertainty: low confidence increases priority
- novelty: recent first_seen increases priority
- recurrence: evidence_count proxy
- operational_impact: urgency field
- research_value: candidate_type specific weight
- research_cost_adjustment: cost penalty

Weights sum to 1.0. All factors normalized 0-1.

## Priority Bands
CRITICAL >=0.75
HIGH >=0.5
MEDIUM >=0.25
LOW <0.25

## False Positive Protection
Prioritization does not use keyword blacklists. Legitimate recruitment/placement/education/corporate communications are not boosted by containing terms like salary, CTC, Google Forms, etc.

## Configuration
Uses `app/intelligence/config.py` `IntelligenceConfig`. No LLM or external network required.

## Determinism
Same input produces same output. Timestamp only used for age calculation, normalized.

## Tests
`tests/intelligence/test_prioritization.py`

Covers basic prioritization, determinism, missing values, false-positive protection, benign infrastructure, multilingual safety.
