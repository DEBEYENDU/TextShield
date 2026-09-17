# RFC-018 Architecture Assessment

## Repository State
- Branch: v2.2-dev
- Version: 2.2.1
- Git status: clean
- Latest commit: 7246c94 docs: add RFC-016 and RFC-017 architecture assessments

## Existing Capabilities

### Core Platform
- Hybrid ML Engine: app/ml_engine/
- RAG Retrieval Pipeline: app/rag/
- LLM Reasoning & Evidence Validation: app/agents/, app/reasoning/
- Behavioral / Social Engineering: app/behavior/
- Multi-Agent Security Reasoning: app/agents/
- Continuous Evaluation & Learning: app/evaluation/
- Adaptive Decision & Evidence Fusion: app/decision/
- Threat Intelligence: app/threat_intel/
- Observability/Audit/Reliability: app/observability/, app/analytics/
- MLOps/Model Lifecycle: app/mlops/
- Multilingual/Transformer Intelligence: app/semantic/
- Real-Time Ingestion/Security Gateway: app/ingestion/
- Threat Graph/Campaign Intelligence: app/graph/
- Threat Actor Attribution/Infrastructure: app/attribution/
- Adaptive Threat Response/Orchestration: app/response/
- Continuous Threat Hunting/Proactive Detection: app/hunting/
- Autonomous Threat Research RFC-017: app/research/

### RFC-017 Implementation State
app/research/ contains:
config.py, enums.py, models.py, repository.py, request_manager.py, planner.py, tasks.py, source_registry.py, collector.py, extractor.py, reliability.py, fusion.py, confidence_engine.py, validator.py, enrichment.py, graph_integration.py, rag_integration.py, llm_agent.py, report_generator.py, scheduler.py, security_privacy.py, evidence_provenance.py, knowledge_lifecycle.py, api.py, cli.py

Implementation audit docs/rfc-017-implementation-audit.md indicates scaffold with in-memory repository, stub integrations, no DB persistence, no real graph/RAG integration, LLM safety broken.

### Existing Integrations
- Threat Graph: app/graph/ – config, models, normalization, entity resolution, API
- Knowledge Graph: app/knowledge_graph/
- RAG: app/rag/
- Hunting: app/hunting/ config/enums/models/observations/repository
- Attribution: app/attribution/
- Threat Intelligence: app/threat_intel/
- Evaluation: app/evaluation/
- MLOps: app/mlops/
- Decision: app/decision/
- Response: app/response/
- Observability: app/observability/

## Reusable Components for RFC-018

Reusable:
- app/research/ candidate generation foundation
- app/graph/ for threat graph integration
- app/knowledge_graph/ for knowledge graph
- app/rag/ for governed RAG ingestion
- app/threat_intel/ source abstraction
- app/attribution/ hypotheses
- app/hunting/ findings
- app/decision/ evidence fusion
- app/evaluation/ test case generation
- app/mlops/ model lifecycle
- app/observability/ metrics/audit
- app/authentication/ JWT security
- app/database/ SQLite schema
- FastAPI API conventions, CLI patterns, Jinja2 frontend

Missing:
- app/intelligence/ package for operations, governance, prioritization
- Candidate engine for research prioritization
- Knowledge gap detection
- Freshness engine
- Knowledge governance lifecycle with controlled promotion
- Contradiction management across sources
- Evidence lineage tracking
- Detection proposal workflow
- Analyst review workflow
- Research-to-RAG governed pipeline
- Research-to-Evaluation pipeline
- Scheduler integration with RFC-012
- API endpoints for intelligence candidates/gaps/governance
- CLI commands for intelligence operations
- Frontend dashboard for Security Intelligence
- Database migrations for intelligence entities

## Integration Points

Database:
Existing app/database/ SQLite with models. New entities required: ResearchCandidate, KnowledgeGap, KnowledgeGovernanceRecord, KnowledgeFreshnessRecord, KnowledgeClaim, ContradictionRecord, DetectionProposal, IntelligenceWorkflow.

API:
Existing app/api/ routes. New endpoints under /api/v1/intelligence/*

CLI:
Existing CLI architecture under app/ commands. Extend with intelligence commands.

Frontend:
Existing Jinja2 templates under app/templates/. Add Security Intelligence section.

Scheduler:
Existing RFC-012 job infrastructure. Extend for intelligence scheduler.

## Security & Privacy Implications
Must preserve trust boundary: external research content is untrusted. No arbitrary network activity, no scanning, no exploitation. LLM cannot fabricate evidence. Source reliability must be tracked. Knowledge promotion must be controlled. Privacy redaction required.

## Performance Implications
Candidate generation, prioritization, freshness checks must be asynchronous. Heavy work must not block synchronous message analysis.

## Backward Compatibility Risks
Existing APIs /api/analysis, /api/history, /api/stats, /api/model-info, /api/knowledge-base must remain functional. No breaking changes to existing research modules.

## RFC Dependency Graph
RFC-018 depends on:
RFC-017 Autonomous Threat Research
RFC-013 Threat Graph
RFC-008 Threat Intelligence
RFC-014 Attribution
RFC-016 Threat Hunting
RFC-015 Response
RFC-009 Observability
RFC-010 MLOps
RFC-012 Ingestion/Scheduler

## Duplicate Architecture Risks
- Do NOT create second Threat Graph
- Do NOT create second Knowledge Graph
- Do NOT create second RAG engine
- Do NOT duplicate research engine
- Extend existing implementations only

## Proposed RFC-018 Architecture

app/intelligence/
  __init__.py
  config.py
  enums.py
  models.py
  schemas.py
  repository.py
  candidates.py
  prioritization.py
  planner.py
  scheduler.py
  freshness.py
  coverage.py
  gaps.py
  dependencies.py
  governance.py
  promotion.py
  expiration.py
  contradiction.py
  validation.py
  confidence.py
  provenance.py
  fusion.py
  graph.py
  rag.py
  evaluation.py
  detections.py
  analyst.py
  feedback.py
  workflow.py
  diagnostics.py
  api.py
  cli.py

Workflow:
Messages → Analysis → Threat Intel/Graph/Attribution/Hunting/Evaluation → Research Candidates → Prioritization → RFC-017 Research Engine → Validation → Reliability + Contradiction → Knowledge Governance → Threat Graph / RAG / Evaluation / Detection Proposals / Analyst Review → Continuous Intelligence State

## Recommended Implementation Order
1. Architecture assessment – done
2. Candidate model + generation
3. Prioritization engine
4. Knowledge gap detection
5. Freshness engine
6. Governance + promotion/demotion/expiration
7. Contradiction management + provenance
8. Threat Graph integration
9. RAG governance integration
10. Evaluation integration
11. Detection proposals
12. Scheduler
13. API
14. CLI
15. Frontend
16. Security hardening
17. Observability
18. Performance
19. Documentation
20. Full regression suite

## Database Implications
New migrations required for intelligence entities. Reversible, tested, compatible.

## API Implications
New /api/v1/intelligence/* endpoints. Existing endpoints unchanged.

## Frontend Implications
Add Security Intelligence dashboard section. Existing pages must remain functional.

## CLI Implications
Extend existing CLI with intelligence commands.

## Conclusion
Existing RFC-017 provides research foundation but lacks operational intelligence, governance, prioritization, and closed-loop control. RFC-018 should extend existing components without duplication, introducing app/intelligence/ for candidate prioritization, knowledge governance, freshness, contradiction management, and controlled closed-loop evolution.
