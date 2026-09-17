# Evidence Engine Guide — TextShield v2.2

## Unified Evidence Integration
Collects from 7 sources: Threat Intelligence, Hybrid ML, LLM Reasoning, RAG Retrieval, Rule Engine, Semantic Analysis, Intent Analysis → `EvidenceGraph` (adjacency-list, provenance chain).

## Components
- `app/evidence/models.py` (`EvidenceItem`, `EvidenceSource`, `EvidenceGraph`)
- `app/evidence/registry.py` (pluggable sources)
- `validator` (schema)
- `confidence.py` (multi-factor: source weight, corroboration, recency, severity, agreement)
- `merger.py` (merge, conflict detection, traceability)
- `graph.py` (adjacent list, `get_provenance_chain`)
- `engine.py` (orchestrates `collect → validate → compute confidence → merge → explain`)
- `explanation.py` (human-readable summaries)
- `app/threat/aggregation` fusion mirrors same logic for threat-only.

## API
`POST /api/v2/evidence/collect`, `GET /api/v2/evidence/{id}`, `GET /graph/{id}`.

## Adding Source
Implement `EvidenceSource` interface, register via `EvidenceRegistry.register()`, add weighting in `confidence.py`.

See `docs/Unified_Evidence.md`.
