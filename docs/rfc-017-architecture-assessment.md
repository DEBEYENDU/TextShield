# RFC-017 Architecture Assessment

## Repository State
- Branch: v2.2-dev
- Version: 2.2.1
- Git status: clean except untracked docs/rfc-016-architecture-assessment.md
- Last commit: ff03886 feat(hunting): add observation store and repository layer

## Existing Relevant Systems

### Intelligence Layers
- RFC-008 Threat Intelligence: app/threat_intel/
- RFC-013 Threat Graph: app/graph/
- RFC-014 Attribution: app/attribution/
- RFC-016 Threat Hunting: app/hunting/ config/enums/models/observations/repository
- RFC-015 Response/Orchestration: app/response/
- RFC-011 Semantic Intelligence: app/semantic/
- RFC-004/005 Behavior/Intent: app/behavior/, app/intent/
- RFC-007 RAG/LLM/Agents: app/rag/, app/agents/
- RFC-010 MLOps: app/mlops/
- RFC-012 Ingestion: app/ingestion/
- RFC-009 Observability/Audit: app/observability/, app/analytics/audit.py

### Decision & Response
- app/decision/ decision_engine, evidence_fusion
- app/response/ policy engine, decision, executor, approval

### Knowledge & Graph
- app/knowledge_graph/ GraphStore, Node, Edge
- app/graph/ threat graph models

### Storage & API
- app/database/ SQLite, models, repositories
- app/api/ routes for analysis, decision, attribution, response, threat_intel
- app/templates/ Jinja2 frontend
- Authentication via app/authentication/manager.py, JWT

## Reusable Components for RFC-017

Reusable:
- Threat Hunting findings from app/hunting/
- Threat Intelligence source abstraction and IOC normalization
- Threat Graph for entity enrichment and relationship validation
- Attribution hypotheses
- RAG knowledge store
- Semantic embeddings
- Evidence provenance from app/evidence/
- Audit/observability pipelines
- Authentication/authorization
- Scheduler via RFC-012 job infrastructure
- FastAPI API conventions, CLI patterns, frontend patterns

Missing:
- app/research/ package
- Research request lifecycle
- Research planner
- Source registry with reliability metadata
- Evidence provenance model with source reliability
- Contradiction engine
- Knowledge fusion layer
- Graph evolution with validation states
- RAG knowledge evolution with provenance
- Research reports
- Research APIs, CLI, Frontend

## Security / Privacy Considerations
Must protect benign infrastructure, avoid unauthorized reconnaissance, maintain provenance, LLM outputs marked as inferred, source reliability tracked, contradictions preserved.

## Implementation Order Proposal
1. Architecture assessment done
2. Config/enums/models/schemas
3. Research request/repository
4. Planner
5. Source registry
6. Evidence/provenance
7. Source reliability & contradiction
8. Knowledge extraction
9. Enrichment layers
10. Fusion
11. Graph/RAG integration
12. LLM/agent assistance with safety
13. Knowledge lifecycle
14. Scheduler
15. APIs
16. CLI
17. Frontend
18. Security hardening
19. Tests & docs

No duplication of existing intelligence systems.
