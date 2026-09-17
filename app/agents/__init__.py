"""Multi-Agent AI Security Reasoning Framework (v4.0 / RFC-005).

Specialized agents independently analyze the same message against shared
context (understanding, behavior, graph, RAG, ML). An orchestrator runs
them in parallel; a consensus engine merges findings into unified evidence.

This is NOT a multi-LLM system: agents are deterministic reasoning modules
built on existing engines, using the LLM provider abstraction only for
optional reasoning enrichment. Nothing here classifies on its own.
"""

from __future__ import annotations

__version__ = "4.0.0"
__rfc__ = "RFC-005"

AGENT_NAMES = [
    "RecruitmentAgent",
    "BankingAgent",
    "GovernmentAgent",
    "PhishingAgent",
    "FraudAgent",
    "BehaviorAgent",
    "LegitimacyAgent",
]
