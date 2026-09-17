# RFC-017 Implementation Audit

## Inspection Summary
- Branch: v2.2-dev
- Version: 2.2.1
- Git status: clean, untracked docs/rfc-016-architecture-assessment.md, docs/rfc-017-architecture-assessment.md
- RFC-017 commits: 5298d29, 911edf2, 9a9f83e, 7219f87
- Files under app/research/: 25 Python modules, all stub implementations with in-memory repository
- Tests: 3 test files, unit tests for model construction, repository CRUD, request manager creation only
- Database: no migrations, no persistence to app/database/, in-memory dicts only
- API: router defined but not mounted in main app; uses isolated ResearchRepository instance per import

## Acceptance-Criteria Audit

### Research Requests
- Creation: PARTIALLY_IMPLEMENTED – manager.create_request works, ID generated, but no validation of request_type, target, scope, no duplicate handling
- Lifecycle states: PARTIALLY_IMPLEMENTED – ResearchState enum defined, status field exists, update_state exists, but no transition validation, no state machine enforcement
- Persistence: MISSING – in-memory dict, no database, no migrations
- Classification: IMPLEMENTED for model, NOT_TESTED for lifecycle

### Planner
- Planner exists: IMPLEMENTED – planner.py returns list of ResearchTask
- Task linking: PARTIALLY_IMPLEMENTED – tasks created with research_id="pending"
- Classification: PARTIALLY_IMPLEMENTED

### Tasks
- Task model: IMPLEMENTED
- Execution: MISSING – tasks.py has TaskExecutor.execute setting status to COMPLETED, no real work, no async, no retry
- Classification: PARTIALLY_IMPLEMENTED

### Source Registry
- Registry model: IMPLEMENTED – SourceRegistry with register/get/list_by_type/update_reliability
- Reliability metadata: IMPLEMENTED – fields present
- Persistence: MISSING – in-memory
- Classification: PARTIALLY_IMPLEMENTED

### Collection & Normalization
- Collector: PARTIALLY_IMPLEMENTED – create Evidence objects, no actual source fetching
- Normalizer: PARTIALLY_IMPLEMENTED – strip/lower only
- Classification: PARTIALLY_IMPLEMENTED

### Extraction
- KnowledgeExtractor.extract_from_evidence: PARTIALLY_IMPLEMENTED – creates KnowledgeItem with fixed entity_type
- No entity recognition, no IOC parsing
- Classification: PARTIALLY_IMPLEMENTED

### Reliability & Contradiction
- ReliabilityEngine.score: PARTIALLY_IMPLEMENTED – simple multiplication
- ContradictionEngine.detect: PARTIALLY_IMPLEMENTED – pairwise claim/value mismatch, no temporal/scope handling
- Classification: PARTIALLY_IMPLEMENTED

### Evidence Fusion
- EvidenceFusionEngine.fuse: PARTIALLY_IMPLEMENTED – averages confidence, no weighting by source reliability/freshness
- Classification: PARTIALLY_IMPLEMENTED

### Confidence & Validation
- ConfidenceEngine.compute: IMPLEMENTED
- EvidenceValidator.validate: PARTIALLY_IMPLEMENTED – threshold 0.5 only
- Classification: PARTIALLY_IMPLEMENTED

### Enrichment
- EnrichmentEngine.enrich: PARTIALLY_IMPLEMENTED – sets attribute enriched=True
- Classification: PARTIALLY_IMPLEMENTED

### Graph Integration
- GraphIntegration.update_graph: MISSING – stub returns fake updated list, does not reuse app/graph/ or app/knowledge_graph/
- No provenance propagation to graph
- Classification: MISSING

### RAG Integration
- RAGIntegration.update_knowledge_store: MISSING – stub returns count, does not integrate with app/rag/
- No provenance, no validation state
- Classification: MISSING

### LLM/Agent Safety
- ResearchLLMAgent.assist: BROKEN – returns fixed hypothesis, can invent evidence, no validation, no safety guards
- No guardrails against prompt injection
- Classification: BROKEN

### Knowledge Lifecycle
- KnowledgeLifecycle.promote/expire: PARTIALLY_IMPLEMENTED – state change only, no expiration logic
- Classification: PARTIALLY_IMPLEMENTED

### Reports
- ResearchReportGenerator.generate: PARTIALLY_IMPLEMENTED – summary string only
- No evidence_summary population, no recommendations logic
- Classification: PARTIALLY_IMPLEMENTED

### Scheduler
- ResearchScheduler.schedule/next_due: PARTIALLY_IMPLEMENTED – in-memory queue, no persistence, no integration with RFC-012 job infrastructure
- No retry/timeout/cancellation
- Classification: PARTIALLY_IMPLEMENTED

### Privacy & Security
- ResearchSecurity.redact_pii: PARTIALLY_IMPLEMENTED – returns "[REDACTED]"
- No actual secret detection, no audit logging
- Classification: PARTIALLY_IMPLEMENTED

### API
- Router defined: IMPLEMENTED
- POST /api/v1/research/request: PARTIALLY_IMPLEMENTED – creates request, no validation, no auth
- GET /api/v1/research/{id}: PARTIALLY_IMPLEMENTED – returns model_dump, no error sanitization
- Not mounted in app – MISSING
- No input validation for missing target, unsupported type, oversized input, duplicate, cancellation, auth
- Classification: PARTIALLY_IMPLEMENTED

### CLI
- cli.py exists with main() creating request – PARTIALLY_IMPLEMENTED
- No commands for list/show/evidence/sources/report/cancel/knowledge/diagnostics/cleanup
- Classification: PARTIALLY_IMPLEMENTED

### Database
- Models: MISSING – no SQLAlchemy models
- Repository: MISSING – in-memory only
- Migrations: MISSING
- Transactions: MISSING
- Classification: MISSING

### Observability
- No integration with app/observability/
- No metrics, logs for research ID, duration, source count, evidence count, contradictions, errors
- Classification: MISSING

### MLOps
- No integration with RFC-006/RFC-010
- No version tracking for research/algorithm/model
- Classification: MISSING

### Frontend
- No frontend integration
- Classification: MISSING

### Offline Mode
- No external source handling, no fallback verification
- Classification: NOT_TESTED

### Performance
- No performance tests, no async execution
- Classification: NOT_TESTED

### Security Tests
- No knowledge poisoning tests
- No false positive regression
- No malicious research regression
- Classification: MISSING

## Trace Execution Path
API request → manager.create_request → in-memory repo create → returns ID
No planner invocation, no task execution, no evidence collection, no fusion, no graph/RAG update, no report generation.

## Persistence Trace
All data stored in Python dicts in ResearchRepository instance. Process restart loses data. No DB.

## Evidence Provenance Trace
Evidence model has provenance dict field, but never populated. No tracking of source reliability history.

## Graph Integration Trace
Stub only, no call to app/graph/ or app/knowledge_graph/.

## RAG Integration Trace
Stub only, no call to app/rag/.

## LLM Integration Trace
Stub returns static hypothesis, no validation, no safety.

## Scheduler Trace
In-memory queue, no background worker.

## Conclusion
RFC-017 implementation is a scaffold with models, enums, config, and in-memory repository stubs. Core workflow is not implemented. Production hardening requirements are not met. Significant gaps in persistence, validation, safety, integration, observability, security, and testing.

Next steps: end-to-end implementation, database migrations, real integrations, safety guards, tests.
