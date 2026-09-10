"""Base agent contract: every agent returns the RFC-005 report shape."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path

from app.agents.context import AgentContext
from app.core.logging import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class BaseAgent(ABC):
    """Specialized security-domain analyst.

    Subclasses implement :meth:`assess` (relevance + findings) while the
    base class enforces the report contract, timing and failure isolation.
    An optional LLM client may enrich ``reasoning``; deterministic findings
    always stand alone so agents work with no LLM configured.
    """

    name: str = "BaseAgent"
    version: str = "1.0.0"
    prompt_file: str = ""  # e.g. "recruitment.md" under prompts/
    timeout_seconds: float = 5.0

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._prompt_cache: str | None = None

    # ------------------------------------------------------- prompt
    @property
    def prompt(self) -> str:
        """Versioned agent prompt text ('' when no prompt file)."""
        if self._prompt_cache is None:
            self._prompt_cache = self._load_prompt()
        return self._prompt_cache

    def _load_prompt(self) -> str:
        if not self.prompt_file:
            return ""
        path = PROMPTS_DIR / self.prompt_file
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Agent %s prompt missing (%s): %s",
                           self.name, self.prompt_file, exc)
            return ""

    # ------------------------------------------------------- analysis
    @abstractmethod
    def assess(self, ctx: AgentContext) -> dict:
        """Return partial report: relevance, findings, risk/trust, action.

        Keys used: ``relevance`` (0..1), ``findings`` (list[str]),
        ``risk_score`` (0..1), ``trust_score`` (0..1),
        ``recommended_action`` (str), ``reasoning`` (str).
        """

    def analyze(self, ctx: AgentContext) -> dict:
        """Run assessment with timing + isolation; always returns full shape."""
        started = time.perf_counter()
        try:
            partial = self.assess(ctx) or {}
        except Exception as exc:
            logger.warning("Agent %s failed: %s", self.name, exc)
            partial = {"relevance": 0.0,
                       "findings": [f"agent error: {exc}"],
                       "risk_score": 0.0, "trust_score": 0.0,
                       "recommended_action": "Manual review (agent error).",
                       "reasoning": "Assessment failed; no opinion."}
        reasoning = str(partial.get("reasoning", ""))
        if self.llm_client is not None and reasoning:
            try:
                enriched = self._llm_enrich(ctx, reasoning)
                if enriched:
                    reasoning = enriched
            except Exception as exc:
                logger.warning("Agent %s LLM enrichment failed: %s", self.name, exc)
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return {
            "name": self.name,
            "version": self.version,
            "confidence": self._confidence(partial),
            "relevance": round(float(partial.get("relevance", 0.0)), 3),
            "findings": list(partial.get("findings", [])),
            "risk_score": round(float(partial.get("risk_score", 0.0)), 3),
            "trust_score": round(float(partial.get("trust_score", 0.0)), 3),
            "recommended_action": str(partial.get("recommended_action", "")),
            "reasoning": reasoning,
            "latency_ms": elapsed_ms,
        }

    # ------------------------------------------------------- helpers
    @staticmethod
    def _confidence(partial: dict) -> float:
        findings = partial.get("findings", [])
        relevance = float(partial.get("relevance", 0.0))
        if not findings:
            return round(0.3 * relevance, 3)
        return round(min(0.95, 0.45 + 0.12 * len(findings) + 0.2 * relevance), 3)

    def _llm_enrich(self, ctx: AgentContext, reasoning: str) -> str:
        """Optional LLM polish of the reasoning string via provider abstraction."""
        system = (self.prompt or f"You are {self.name}, a security analyst.")[:2000]
        user = (f"Message: {ctx.text[:800]}\nDraft analysis: {reasoning}\n"
                f"Refine into 2 sentences, keep all factual claims.")
        try:
            text = self.llm_client.complete(system, user)
        except TypeError:
            text = self.llm_client.complete(f"{system}\n{user}")
        return text.strip()[:600] if text and text.strip() else ""
