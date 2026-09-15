# RFC-014 Threat Actor Attribution & Infrastructure Intelligence

## Overview
Extends RFC-013 Threat Graph with actor profiling, infrastructure intelligence, evidence aggregation, hypothesis generation, and timeline reconstruction.

## Modules
- `app/attribution/config.py` - Configuration
- `app/attribution/models.py` - Pydantic models
- `app/attribution/actor_profile.py` - Actor profiling
- `app/attribution/infrastructure_intel.py` - IOC ingestion and infrastructure nodes
- `app/attribution/evidence_aggregator.py` - Evidence scoring
- `app/attribution/hypothesis_engine.py` - Hypothesis generation
- `app/attribution/attribution_engine.py` - Orchestrator
- `app/attribution/timeline_reconstruction.py` - Temporal analysis
- `app/attribution/api.py` - FastAPI router
- `app/attribution/privacy.py` - Privacy controls
- `app/attribution/security.py` - Access controls

## API
POST /api/v1/attribution/analyze
GET /api/v1/attribution/health

## Integration
Reuses `app/knowledge_graph`, `app/graph`, `app/threat_intel`, `app/semantic`, `app/evidence`, `app/decision`.
No duplicate graph stores.
