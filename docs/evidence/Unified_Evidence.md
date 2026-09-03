# Unified Evidence Integration Engine

## Architecture
- `models.py`: `EvidenceItem`, `EvidenceSource` enum, `EvidenceGraph`
- `registry.py`: `EvidenceRegistry` – source registration/discovery
- `validator.py`: `EvidenceValidator` – schema validation
- `confidence.py`: `EvidenceConfidence` – multi-factor confidence calculation
- `merger.py`: `EvidenceMerger` – merge, conflict detection, traceability
- `graph.py`: `EvidenceGraph` – adjacency list, provenance chains
- `engine.py`: `EvidenceEngine` – orchestrate collection from all registered sources
- `explanation.py`: `EvidenceExplanation` – human-readable summaries

## Evidence Model
Each `EvidenceItem` contains:
- `evidence_id`: UUID for traceability
- `source`: `EvidenceSource` enum (threat_intelligence, hybrid_ml, llm_reasoning, rag_retrieval, rule_engine, semantic_analysis, intent_analysis, custom)
- `timestamp`: UTC datetime
- `confidence`: float 0.0–1.0
- `weight`: source-specific weight
- `summary`: human-readable summary
- `raw_evidence`: original unprocessed data
- `structured_evidence`: parsed/normailzed dict
- `supporting_artifacts`: list of artifact IDs/references
- `metadata`: key-value pairs

## Evidence Graph
- Adjacency-list graph preserving full traceability
- Nodes: `evidence_<source>` + merged node
- Directed links: source → merged evidence
- `trace_from(node_id)` returns chain of provenance (source → … → evidence)
- `paths_to(target_type)` finds all routes to a given node type
- Frontend can display: which subsystem produced each piece, when, why, supporting artifacts

## Registry
- `EvidenceRegistry` maintains mapping of source name → `EvidenceSource` enum
- `register(name, source, factory)` / `unregister(name)` / `list_sources()`
- Enables pluggable addition of new evidence modules without code changes to existing ones

## Merger
- `EvidenceMerger.merge(items)` combines multiple evidence items into one
- Groups by source, averages weighted confidence, picks most recent timestamp
- Unites supporting artifacts, merges structured evidence (key-level prefer-recent)
- `detect_conflicts(items)` returns dict with `has_conflicts`, `status_distribution`, `conflicting_sources`
- Conflict detection: if some evidence says "malicious" and some says "benign"

## Confidence
- `EvidenceConfidence.calculate(items, source_reliabilities, now)` returns float in [0.0, 1.0]
- Factors:
  1. **Count factor** – min(n/5, 1.0) – diminishing returns after 5 items
  2. **Weighted agreement** – average confidence × source reliability
  3. **Freshness** – exponential decay half-life 24h since newest timestamp
  4. **Completeness** – fraction of required fields present across items
- Weighted combination: 35% count + 30% agreement + 20% freshness + 15% completeness

## API
- **POST** `/api/v2/evidence/collect` – body: `{analysis_id: string, force: bool}`
  - Collects evidence from all registered subsystems
  - Returns unified `EvidenceItem` JSON
- **GET** `/api/v2/evidence/{analysis_id}` – returns the unified evidence item
- **GET** `/api/v2/evidence/graph/{analysis_id}` – returns `{nodes: {id: {type, source, timestamp}}, links: {id: [neighbour_ids]}}`
- **POST** `/api/v2/evidence/explain` – body: `{analysis_id: string}` – human-readable explanation

## Configuration
- New evidence sources register via `register_evidence_source(name, EvidenceSource)` – no code changes to engine required
- Source reliabilities supplied optionally to `merge()` / `calculate()`
- Confidence/conflict thresholds tunable per deployment

## Examples
```python
engine = EvidenceEngine()
merged = engine.collect("analysis_001")
# merged.confidence in [0,1]
# merged.source is an EvidenceSource enum
# merged.evidence_id is a UUID

# Provenance chain
chain = engine.graph.trace_from(merged.evidence_id)
# chain[i]["source"].value == "threat_intelligence" etc.

# Conflict detection
conflicts = engine.graph.detect_conflicts([merged])
# conflicts["has_conflicts"] True if opposing conclusions present
```

## Known Limitations
- Confidence/conflict formulas are heuristic; production should calibrate on real data
- Only five confidence factors modelled; additional signals can be added
- No integration with the Decision Engine (per RFC‑008 stop condition)
- Frontend UI not modified

## Remaining RFC Dependencies
- Decision Engine integration (excluded by design)
- Additional evidence modules (ML, LLM, RAG rule outputs) – registerable via the registry
- Dashboard / UI changes
- Front-end components to display provenance chains and conflict detection results