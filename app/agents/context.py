"""Shared agent context: built once, read by every agent.

No duplicate RAG retrieval, no duplicate extraction — the orchestrator
assembles understanding, behavior, graph, RAG, ML and indicator outputs
into one bundle handed to all agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentContext:
    """Everything an agent may need; all fields optional-tolerant."""

    text: str = ""
    sender: str = ""
    subject: str = ""
    # v4 understanding (RFC-001)
    profile: dict = field(default_factory=dict)
    entities: dict = field(default_factory=dict)
    threat: dict = field(default_factory=dict)
    legitimacy: dict = field(default_factory=dict)
    # v4 behavior (RFC-004)
    behavior: dict = field(default_factory=dict)
    behavior_profile: dict = field(default_factory=dict)
    # v4 knowledge graph (RFC-003)
    graph_verdict: dict = field(default_factory=dict)
    graph_expansion_terms: list = field(default_factory=list)
    # pipeline evidence
    ml_label: str = ""
    ml_confidence: float = 0.0
    indicators: list = field(default_factory=list)
    urls: list = field(default_factory=list)
    rag_evidence: list = field(default_factory=list)
    risk_level: str = ""
    risk_score: float = 0.0
    # memory recall (filled by orchestrator)
    similar_past: list = field(default_factory=list)

    # ------------------------------------------------------- convenience
    @property
    def category(self) -> str:
        return str(self.profile.get("category", "Unknown"))

    @property
    def intent(self) -> str:
        return str(self.profile.get("intent", "Inform"))

    def threat_families(self) -> set[str]:
        return {str(i.get("family", "")).lower()
                for i in self.threat.get("indicators", [])}

    def indicator_names(self) -> set[str]:
        return {str(i.get("indicator", "")).lower()
                for i in self.indicators}

    def entity_values(self, group: str) -> list[str]:
        items = self.entities.get(group, []) or []
        return [str(i.get("value", "")) if isinstance(i, dict) else str(i)
                for i in items]

    def has_url(self) -> bool:
        return bool(self.entity_values("urls") or self.urls)

    def to_dict(self) -> dict:
        return {
            "text": self.text[:500], "sender": self.sender,
            "category": self.category, "intent": self.intent,
            "threat_score": self.profile.get("threat_score", 0.0),
            "trust_score": self.profile.get("trust_score", 0.0),
            "ml_label": self.ml_label, "risk_level": self.risk_level,
        }
