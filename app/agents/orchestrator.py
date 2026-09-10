"""Agent orchestrator: shared context, parallel execution, timeouts,
failure isolation, memory recall and persistence."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from app.agents.base_agent import BaseAgent
from app.agents.consensus import consensus_engine
from app.agents.context import AgentContext
from app.agents.evidence import fuse_evidence
from app.agents.memory import AgentMemory, agent_memory
from app.agents.registry import default_registry
from app.agents.report import build_report
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Run all agents against one shared context and unify the findings."""

    def __init__(self, registry=None, memory: AgentMemory | None = None,
                 max_workers: int = 7, agent_timeout: float = 5.0,
                 llm_client=None):
        self.registry = registry or default_registry
        self.memory = memory or agent_memory
        self.max_workers = max_workers
        self.agent_timeout = agent_timeout
        self.llm_client = llm_client

    # ------------------------------------------------------- context
    @staticmethod
    def build_context(analysis: dict, text: str = "", sender: str = "",
                      subject: str = "") -> AgentContext:
        understanding = analysis.get("understanding", {}) or {}
        profile = analysis.get("message_profile", {}) or {}
        behavior = analysis.get("behavior", {}) or {}
        graph = analysis.get("knowledge_graph", {}) or {}
        return AgentContext(
            text=text or str(analysis.get("message", "")),
            sender=sender, subject=subject,
            profile=profile,
            entities=understanding.get("entities", {}),
            threat=understanding.get("threat", {}),
            legitimacy=understanding.get("legitimacy", {}),
            behavior=behavior,
            behavior_profile=analysis.get("behavior_profile", {}),
            graph_verdict={"known_organizations": graph.get("known_organizations", []),
                           "campaign_matches": graph.get("campaign_matches", [])},
            graph_expansion_terms=graph.get("expansion_terms", []),
            ml_label=str(analysis.get("classification", "")),
            ml_confidence=float(analysis.get("confidence", 0.0) or 0.0),
            indicators=analysis.get("indicators", []),
            urls=analysis.get("urls", []),
            rag_evidence=analysis.get("rag_evidence", []),
            risk_level=str(analysis.get("risk_level", "")),
            risk_score=float(analysis.get("risk_score", 0.0) or 0.0),
        )

    # ------------------------------------------------------- execution
    def run(self, ctx: AgentContext,
            only: list[str] | None = None) -> dict:
        """Execute agents in parallel; return the unified evidence report."""
        started = time.perf_counter()
        try:
            ctx.similar_past = self.memory.recall_similar(ctx.text)
        except Exception as exc:
            logger.warning("Agent memory recall failed: %s", exc)
        agents = self.registry.instantiate(llm_client=self.llm_client, only=only)
        reports = self._run_parallel(agents, ctx)
        consensus = consensus_engine.reach_consensus(
            reports, ml_label=ctx.ml_label, ml_confidence=ctx.ml_confidence)
        fused = fuse_evidence(
            reports,
            {"graph_reasons": (ctx.graph_verdict or {}).get("reasons", []) if isinstance(ctx.graph_verdict, dict) else [],
             "behavior_triggers": (ctx.behavior_profile or {}).get("psychological_triggers", [])},
            rag_evidence=ctx.rag_evidence)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        report = build_report(ctx.to_dict() | {"entities": ctx.entities},
                              reports, consensus, fused, elapsed_ms)
        try:
            self.memory.remember(
                ctx.text, ctx.category, report["overall_risk"],
                consensus["consensus"],
                {r["name"]: r["confidence"] for r in reports},
                retrieval_terms=ctx.graph_expansion_terms)
        except Exception as exc:
            logger.warning("Agent memory persist failed: %s", exc)
        logger.info("Agents: %d ran, consensus=%s risk=%s in %.1fms",
                    len(reports), consensus["consensus"],
                    report["overall_risk"], elapsed_ms)
        return report

    def _run_parallel(self, agents: list[BaseAgent],
                      ctx: AgentContext) -> list[dict]:
        reports: list[dict] = []

        def _safe_run(agent: BaseAgent) -> dict:
            try:
                return agent.analyze(ctx)
            except Exception as exc:  # never let one agent sink the run
                logger.warning("Agent %s crashed: %s", agent.name, exc)
                return {"name": agent.name, "version": agent.version,
                        "confidence": 0.0, "relevance": 0.0,
                        "findings": [f"agent crashed: {exc}"],
                        "risk_score": 0.0, "trust_score": 0.0,
                        "recommended_action": "Manual review (agent crash).",
                        "reasoning": "Agent failed; no opinion.",
                        "latency_ms": 0.0}

        with ThreadPoolExecutor(max_workers=max(1, self.max_workers)) as pool:
            futures = {pool.submit(_safe_run, agent): agent for agent in agents}
            for future, agent in futures.items():
                try:
                    reports.append(future.result(timeout=self.agent_timeout))
                except FutureTimeout:
                    logger.warning("Agent %s timed out after %.1fs",
                                   agent.name, self.agent_timeout)
                    reports.append({"name": agent.name, "version": agent.version,
                                    "confidence": 0.0, "relevance": 0.0,
                                    "findings": ["agent timed out"],
                                    "risk_score": 0.0, "trust_score": 0.0,
                                    "recommended_action": "Manual review (timeout).",
                                    "reasoning": "Agent timed out; no opinion.",
                                    "latency_ms": self.agent_timeout * 1000.0})
        reports.sort(key=lambda r: r.get("name", ""))
        return reports


agent_orchestrator = AgentOrchestrator()
