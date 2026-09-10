"""Benchmark runner: run named collections with one command.

Collections: banking, education, government, healthcare, corporate,
courier, recruitment, phishing, fraud, bec (plus any data/eval/*.json).
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.evaluation import COLLECTIONS
from app.evaluation.dataset import DatasetManager
from app.evaluation.evaluator import EvaluationEngine
from app.evaluation.reports import summarize_run

logger = get_logger(__name__)


class BenchmarkRunner:
    """One-command benchmark execution over collections."""

    def __init__(self, with_agents: bool = False):
        self.datasets = DatasetManager()
        self.engine = EvaluationEngine(with_agents=with_agents)

    def available(self) -> list[str]:
        return self.datasets.collections() or list(COLLECTIONS)

    def run_collection(self, name: str, run_name: str | None = None) -> dict:
        samples = self.datasets.load_collection(name)
        logger.info("Benchmark '%s': %d samples", name, len(samples))
        run = self.engine.evaluate(samples, run_name=run_name or f"bench-{name}")
        summary = summarize_run(run)
        return {"run": run, "summary": summary}

    def run_all(self, collections: list[str] | None = None) -> dict:
        names = collections or self.available()
        results = {}
        for name in names:
            try:
                results[name] = self.run_collection(name)
            except Exception as exc:
                logger.warning("Collection %s failed: %s", name, exc)
                results[name] = {"error": str(exc)[:200]}
        return results


def run_benchmark(collections: list[str] | None = None,
                  with_agents: bool = False) -> dict:
    """Convenience entry point used by the CLI."""
    return BenchmarkRunner(with_agents=with_agents).run_all(collections)
