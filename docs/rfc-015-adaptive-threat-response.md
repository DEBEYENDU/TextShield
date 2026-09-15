# RFC-015 Adaptive Threat Response & Automated Security Orchestration

## Overview
Adds controlled response layer above decision engine. Supports MONITOR → WARN → REVIEW → QUARANTINE → BLOCK escalation with safety, reversibility, approval, verification, rollback.

## Architecture
Response engine sits after Decision Engine and before audit.

## Key Components
app/response/
- config.py
- models.py
- policy_engine.py
- decision.py
- executor.py
- approval.py
- rollback.py
- api.py

API:
POST /api/v1/response/evaluate
GET /api/v1/response/health

Policy types: CONSERVATIVE, BALANCED, AGGRESSIVE, ENTERPRISE, RESEARCH, CUSTOM

Safety principles enforced: conservative defaults, dry-run, approval for high-impact, idempotency, audit.

## Integration
Reuses Decision Engine, Risk Engine, Threat Intelligence, Threat Graph, Attribution, Audit, Observability, Auth.

## Tests
tests/response/test_response.py
