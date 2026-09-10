"""Evaluation engine: run the full pipeline per sample and store complete
records (expected vs predicted, threat/trust, agents, consensus, LLM
output, RAG evidence). Never retrains — records are evidence for later."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from app.core.logging import get_logger
from app.evaluation import RUNS_DIR
from app.evaluation.dataset import EvalSample
from app.evaluation.versioning import fingerprint, fingerprint_id

logger = get_logger(__name__)


class EvaluationEngine:
    """Execute samples through analysis (+ optional agents) and record."""

    def __init__(self, runs_dir: str | Path = RUNS_DIR, with_agents: bool = False):
        self.runs_dir = Path(runs_dir)
        self.with_agents = with_agents

    def evaluate(self, samples: list[EvalSample],
                 run_name: str | None = None) -> dict:
        from app.schemas.analysis import AnalyzeRequest
        from app.services import analysis_service

        run_id = run_name or f"run-{uuid.uuid4().hex[:8]}"
        fp = fingerprint()
        records: list[dict] = []
        for sample in samples:
            started = time.perf_counter()
            try:
                result = analysis_service.analyze(
                    AnalyzeRequest(message=sample.message), store_history=False)
                record = self._record_from_result(sample, result)
            except Exception as exc:
                logger.warning("Sample %s failed: %s", sample.id, exc)
                record = {"id": sample.id, "expected": sample.expected_label,
                          "predicted": "ERROR", "confidence": 0.0,
                          "message": sample.message[:200],
                          "message_type": sample.message_type,
                          "collection": sample.collection,
                          "difficulty": sample.difficulty,
                          "error": str(exc)[:200]}
            record["inference_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
            records.append(record)
        run = {"run_id": run_id, "fingerprint": fp,
               "fingerprint_id": fingerprint_id(fp),
               "with_agents": self.with_agents,
               "n_samples": len(records), "records": records}
        self._save_run(run)
        return run

    # ------------------------------------------------------- records
    def _record_from_result(self, sample: EvalSample, result: dict) -> dict:
        profile = result.get("message_profile", {}) or {}
        understanding = result.get("understanding", {}) or {}
        threat = understanding.get("threat", {}) or {}
        agent_opinions = {}
        consensus = None
        if self.with_agents:
            try:
                from app.agents.orchestrator import AgentOrchestrator

                orch = AgentOrchestrator()
                ctx = orch.build_context(result, text=sample.message)
                report = orch.run(ctx)
                consensus = report.get("consensus")
                for rep in report.get("agent_reports", []):
                    agent_opinions[rep["name"]] = {
                        "risk_score": rep.get("risk_score", 0.0),
                        "trust_score": rep.get("trust_score", 0.0),
                        "confidence": rep.get("confidence", 0.0)}
            except Exception as exc:
                logger.warning("Agents failed for %s: %s", sample.id, exc)
        return {
            "id": sample.id,
            "expected": sample.expected_label,
            "predicted": result.get("classification", "ERROR"),
            "confidence": float(result.get("confidence", 0.0) or 0.0),
            "spam_score": float(result.get("confidence", 0.0) or 0.0)
            if result.get("classification") == "SPAM"
            else round(1 - float(result.get("confidence", 0.0) or 0.0), 4),
            "message": sample.message[:200],
            "message_type": profile.get("category", sample.message_type),
            "intent": profile.get("intent", sample.intent),
            "collection": sample.collection,
            "difficulty": sample.difficulty,
            "threat_score": float(profile.get("threat_score", 0.0) or 0.0),
            "trust_score": float(profile.get("trust_score", 0.0) or 0.0),
            "threat_families": sorted({str(i.get("family", ""))
                                       for i in threat.get("indicators", []) if i.get("family")}),
            "agent_opinions": agent_opinions,
            "consensus": consensus,
            "llm_output": str(result.get("explanation", ""))[:300],
            "llm_source": result.get("explanation_source", ""),
            "rag_evidence": [{"source": e.get("source"), "score": e.get("score"),
                              "category": e.get("category")}
                             for e in (result.get("rag_evidence", []) or [])[:5]],
            "risk_level": result.get("risk_level", ""),
        }

    # ------------------------------------------------------- persistence
    def _save_run(self, run: dict) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{run['run_id']}.json"
        path.write_text(json.dumps(run, indent=1, default=str), encoding="utf-8")
        return path

    def load_run(self, run_id: str) -> dict:
        path = self.runs_dir / f"{run_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[dict]:
        runs = []
        if not self.runs_dir.exists():
            return runs
        for path in sorted(self.runs_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                records = data.get("records", [])
                runs.append({"run_id": data.get("run_id", path.stem),
                             "fingerprint_id": data.get("fingerprint_id"),
                             "n_samples": len(records),
                             "with_agents": data.get("with_agents", False)})
            except Exception:
                continue
        return runs
