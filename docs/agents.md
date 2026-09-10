# TextShield v4.0 — Multi-Agent Security Reasoning (RFC-005)

Seven specialized agents analyze the same message against one shared
context; an orchestrator runs them in parallel and a consensus engine
merges their findings. Deterministic — not a multi-LLM system. Agents use
the LLM provider abstraction only for optional reasoning enrichment.

## Architecture

```text
analysis ─▶ AgentContext (shared: profile, entities, threat, behavior,
│                         graph, RAG, ML — built once, no refetch)
│
├─▶ RecruitmentAgent ─┐
├─▶ BankingAgent ─────┤
├─▶ GovernmentAgent ──┤ parallel, per-agent
├─▶ PhishingAgent ────┤ timeout, isolated
├─▶ FraudAgent ───────┤ failures
├─▶ BehaviorAgent ────┤
└─▶ LegitimacyAgent ──┘
         │
         ▼
ConsensusEngine (relevance × confidence weights, conflict rules,
                 strong-alarm floor) ─▶ EvidenceFusion ─▶ Report
```

## Agent lifecycle

`assess(ctx)` → partial (relevance, findings, risk/trust, action,
reasoning) → `analyze()` enforces the report contract, times the run,
optionally enriches reasoning via LLM → orchestrator collects →
consensus → fusion → report → memory persisted.

## Consensus model

Weighted merge of risk/trust/confidence; conflict notes when ML and
agents disagree (contested verdicts); a strong-alarm floor keeps any
high-relevance domain alarm (risk ≥ 0.7) from being averaged away.

## Evidence fusion

Positive / negative / uncertain buckets from relevance-weighted opinions,
plus supporting RAG documents, case studies, graph reasons, behavior
triggers and per-agent opinion cards.

## Prompt design

Each agent owns a versioned prompt under `app/agents/prompts/*.md`
documenting role, scope, signals and the output contract. Prompts feed the
optional LLM enrichment path and serve as living specifications.

## Extending agents

```python
from app.agents.base_agent import BaseAgent
from app.agents.registry import register

@register
class HealthcareAgent(BaseAgent):
    name = "HealthcareAgent"
    prompt_file = "healthcare.md"  # add under prompts/
    def assess(self, ctx): ...
```

No existing code changes required — the orchestrator picks up registered
agents automatically.

## Performance

Shared context (no duplicate retrieval), thread-pool parallelism,
regex/heuristic agents: ~1.8 ms agents-only, ~21 ms full pipeline on the
15-case benchmark — far inside the 700 ms target.
