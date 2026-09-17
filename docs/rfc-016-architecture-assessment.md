# RFC-016 Architecture Assessment

## Repository State
- Branch: v2.2-dev
- Version: 2.2.1
- Git status: clean
- Last commit: 0ec9b95 feat(response): implement RFC-015 Adaptive Threat Response foundation

## Existing Relevant Systems

### Decision / Risk / Response
- app/decision/ decision_engine, evidence_fusion, risk_engine
- app/response/ config, models, policy_engine, decision, executor, approval, rollback
- RFC-015 implemented

### Threat Intelligence
- app/threat_intel/ extractor, normalizer, cache, aggregator, providers, reputation
- RFC-008 implemented

### Threat Graph / Campaign
- app/graph/ models, normalization, entity_resolution, campaign, correlation, temporal, clustering
- RFC-013 implemented

### Attribution
- app/attribution/ actor_profile, infrastructure_intel, evidence_aggregator, hypothesis_engine, attribution_engine
- RFC-014 implemented

### Semantic Intelligence
- app/semantic/ multilingual, transformer, embeddings, hinglish, transliteration
- RFC-011 implemented

### Ingestion
- app/ingestion/ queue, worker, connectors, webhook, bulk, audit
- RFC-012 implemented

### Knowledge Graph
- app/knowledge_graph/ GraphStore, Node, Edge, entity linker
- RFC-003

### Behavior / Intent
- app/behavior/, app/intent/
- RFC-004/005

### RAG / LLM
- app/rag/, app/agents/
- RFC-007

### Hybrid ML / MLOps
- app/ml/, app/ml_engine/, app/mlops/
- RFC-010

### Observability / Audit
- app/observability/, app/analytics/audit.py
- RFC-009

### Authentication / Authorization
- app/authentication/manager.py, JWT settings

### Database
- app/database/ SQLite default, models, repositories

### API / Frontend / CLI
- app/api/routes_*, app/templates/*, scripts/

## Reusable Components for RFC-016

Reusable:
- Historical analysis data via app/services/history_service, app/database
- Threat Intelligence IOC extraction
- Threat Graph for pattern / infrastructure reuse
- Attribution hypotheses
- Semantic embeddings from app/semantic
- Behavior engine signals
- Decision evidence
- Response layer for findings escalation
- Audit/observability pipelines
- Scheduler via RFC-012 job infrastructure
- FastAPI API conventions
- Jinja2 frontend conventions

Missing:
- Observation store model for hunting
- Pattern discovery engine
- Anomaly detection engine
- Semantic / behavioral clustering for hunting
- IOC / infrastructure reuse hunting
- Temporal analysis engine
- Campaign discovery hypothesis generation
- Emerging threat detection
- Finding / hypothesis lifecycle management
- Hunting scheduler
- Hunting APIs
- Hunting frontend

## Database Considerations
Existing models in app/database/models.py. New entities needed:
hunting_observations, hunting_patterns, hunting_anomalies, hunting_findings, hunting_hypotheses, hunting_jobs, hunting_recommendations, hunting_feedback

## Security / Privacy
Reuse existing privacy controls, audit logging, authorization. Benign infrastructure protection required for Google Forms, Microsoft Forms, CDNs, job portals, university domains.

## Implementation Plan
Phase 1: Assessment done
Phase 2: config/enums/models/schemas
Phase 3: observation layer
Phase 4: pattern discovery
Phase 5: anomaly detection
Phase 6: semantic/behavioral clustering
Phase 7: IOC/infrastructure hunting
Phase 8: temporal analysis
Phase 9: campaign discovery
Phase 10: emerging threat detection
Phase 11: finding/hypothesis engine
Phase 12: scoring/confidence
Phase 13: recommendations/feedback
Phase 14: scheduler
Phase 15: APIs
Phase 16: CLI
Phase 17: Frontend
Phase 18: Security/observability hardening
Phase 19: Tests & benchmarks
Phase 20: Docs

No duplicates with existing RFCs. Hunting layer sits above decision/response, feeds back via recommendations.
