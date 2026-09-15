# RFC-015 Architecture Assessment

## Repository State
- Branch: v2.2-dev
- Version: 2.2.1
- Git status: clean
- Last commit: 2b3aac9 feat(semantic): add RFC-011 semantic intelligence modules and observability metrics

## Existing Systems Overview

### Decision / Risk
- app/decision/decision_engine.py
- app/decision/evidence_fusion.py
- app/decision/risk_engine (app/services/risk_engine.py)
- RiskFactors, RiskEngine classes exist
- DecisionOutput, Explanation, Recommendation models present

### Threat Intelligence
- app/threat_intel/ with extractor, normalizer, cache, aggregator, providers
- IOC extraction for URL/domain/IPv4/IPv6/email/hashes
- Async lookup engine, reputation aggregation

### Threat Graph / Campaign Intelligence
- app/graph/ with config, models, normalization, entity_resolution, campaign, correlation, temporal, clustering
- RFC-013 foundation present, placeholders partially filled

### Attribution Intelligence
- app/attribution/ implemented per RFC-014
- ActorProfile, InfrastructureIntel, EvidenceAggregator, HypothesisEngine, AttributionEngine

### Knowledge Graph
- app/knowledge_graph/ with GraphStore, Node, Edge, entity linker
- RFC-003 implementation

### Semantic Intelligence
- app/semantic/ with multilingual, transformer, embeddings, RAG integration, Hinglish, transliteration
- RFC-011 implemented

### Ingestion
- app/ingestion/ with queue, worker, connectors, webhook, bulk, audit, security
- RFC-012 implemented

### Observability / Audit
- app/observability/ with metrics, audit, logging, tracing, health
- app/analytics/audit.py, app/ingestion/audit.py

### Authentication / Authorization
- app/authentication/manager.py
- JWT settings in app/core/settings.py
- Roles: Admin, Analyst, Developer, ReadOnly, Guest

### Database
- app/database/ with SQLite default
- Models in app/database/models.py
- Repositories pattern

### API
- app/api/routes_* with analysis, decision, evaluation, history, knowledge, stats, system, threat_intel, attribution
- FastAPI app in app/main.py

### Frontend
- app/templates/*.html Jinja2
- Pages: index, analyze, history, analytics, knowledge_base, dashboard, evidence

### Tests
- tests/ with attribution, graph, ingestion, evidence, etc.

## Reusable Components for RFC-015

Reusable:
- Decision Engine + Risk Engine + Evidence Fusion
- Threat Intelligence IOC extraction and cache
- Threat Graph models and storage
- Attribution Engine and actor profiles
- Knowledge Graph store
- Audit and Observability pipelines
- Authentication / JWT / RBAC
- Database models and repositories
- FastAPI API conventions
- Jinja2 frontend conventions
- Settings and configuration system
- Async ingestion pipeline

Required Extensions:
- Response decision model
- Policy engine with versioning
- Action planner and executor
- Approval workflow
- Verification and rollback
- Dry-run / shadow mode
- Response history storage
- Response API endpoints
- Response Center UI

Potential Conflicts:
- No existing response engine; no duplicate decision/risk logic needed
- Ensure action execution does not mutate graph entities
- Response actions must be separate from classification

Database Changes:
- New tables: response_decisions, response_actions, response_action_events, response_approvals, response_policies, response_rollbacks

API Changes:
- New routes under /api/v1/response/*

Frontend Changes:
- Response Center page, action detail, approval UI, dry-run UI

Security Risks:
- Unauthorized action execution
- Policy injection
- LLM/agent direct execution
- Replay attacks
- Scope escalation

Testing Strategy:
- Unit tests for models, policy, planner, executor
- Integration tests with decision engine
- Security tests for auth, authorization, injection
- False positive tests for legitimate recruitment/job messages
- Idempotency, rollback, verification tests
- LLM safety tests

Implementation Sequence:
1. Foundation models/config/enums
2. Policy engine
3. Response decision & planning
4. Action framework & executor
5. Approval workflow
6. Verification & rollback
7. Integration with existing systems
8. API & Frontend
9. Security hardening
10. Evaluation & docs

## Conclusion
Repository is ready for RFC-015. No duplicate implementations needed. Reuse existing decision, risk, threat intel, graph, attribution, audit, observability, auth, DB, API, frontend patterns.
