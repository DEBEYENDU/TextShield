"""RFC-005 tests: registry, orchestrator, consensus, fusion, parallel
execution, prompt loading, benchmark suite and regression guards."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.consensus import ConsensusEngine
from app.agents.context import AgentContext
from app.agents.evidence import fuse_evidence
from app.agents.memory import AgentMemory
from app.agents.orchestrator import AgentOrchestrator
from app.agents.registry import AgentRegistry, default_registry
from app.agents.report import build_report
from app.agents.specialists import ALL_AGENTS

BENCH = json.loads((Path(__file__).resolve().parent.parent
                    / "data" / "agent_benchmark.json").read_text(encoding="utf-8"))

CAMPUS = ("Dear Students, Technolearn placement cell announces a campus drive "
          "on 12th March. Register via the Google Form link. No fees.")
FAKE_SBI = ("URGENT: State Bank of India KYC suspended! Verify your login at "
            "http://bit.ly/sbi-kyc now and share OTP within 2 hours.")


def _analysis(text: str) -> dict:
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    return analysis_service.analyze(AnalyzeRequest(message=text),
                                    store_history=False)


def _report(text: str) -> dict:
    analysis = _analysis(text)
    orch = AgentOrchestrator()
    return orch.run(orch.build_context(analysis, text=text))


# ------------------------------------------------------------ registry
def test_registry_has_seven_agents():
    assert len(default_registry) == 7
    for name in ("RecruitmentAgent", "BankingAgent", "GovernmentAgent",
                 "PhishingAgent", "FraudAgent", "BehaviorAgent",
                 "LegitimacyAgent"):
        assert default_registry.get(name) is not None


def test_registry_plugin_registration_no_code_change():
    registry = AgentRegistry()

    class HealthcareAgent(BaseAgent):
        name = "HealthcareAgent"

        def assess(self, ctx):
            return {"relevance": 0.1, "findings": [], "risk_score": 0.0,
                    "trust_score": 0.5, "recommended_action": "",
                    "reasoning": "plugin"}

    registry.register(HealthcareAgent)
    assert registry.get("HealthcareAgent") is HealthcareAgent
    assert "HealthcareAgent" in registry.names()
    assert registry.unregister("HealthcareAgent") is True


def test_agent_report_contract():
    agents = default_registry.instantiate()
    assert len(agents) == 7
    ctx = AgentContext(text=CAMPUS)
    for agent in agents:
        report = agent.analyze(ctx)
        for key in ("name", "confidence", "findings", "risk_score",
                    "trust_score", "recommended_action", "reasoning"):
            assert key in report, f"{agent.name} missing {key}"
        assert 0.0 <= report["risk_score"] <= 1.0
        assert 0.0 <= report["trust_score"] <= 1.0


def test_prompt_loading_versioned():
    agents = default_registry.instantiate()
    loaded = [a for a in agents if a.prompt_file and a.prompt]
    assert len(loaded) >= 6  # six required prompt files, all present
    assert all("v1.0.0" in a.prompt or "v1" in a.prompt for a in loaded)


# ------------------------------------------------------------ orchestrator
def test_orchestrator_runs_all_agents_parallel():
    analysis = _analysis(CAMPUS)
    orch = AgentOrchestrator()
    ctx = orch.build_context(analysis, text=CAMPUS)
    assert ctx.category and ctx.ml_label in {"SPAM", "HAM"}  # shared context
    start = time.perf_counter()
    report = orch.run(ctx)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    assert len(report["agent_reports"]) == 7
    assert report["latency_ms"] < 5000.0
    assert elapsed_ms < 30000.0  # full pipeline incl. analysis stays sane


def test_orchestrator_isolates_failures():
    class BoomAgent(BaseAgent):
        name = "BoomAgent"

        def assess(self, ctx):
            raise RuntimeError("boom")

    orch = AgentOrchestrator()
    reports = orch._run_parallel([BoomAgent()], AgentContext(text="hi"))
    assert reports[0]["relevance"] == 0.0
    assert "boom" in reports[0]["findings"][0]


def test_orchestrator_subset_selection():
    analysis = _analysis(CAMPUS)
    orch = AgentOrchestrator()
    ctx = orch.build_context(analysis, text=CAMPUS)
    report = orch.run(ctx, only=["PhishingAgent", "LegitimacyAgent"])
    assert sorted(report["agents"]) == ["LegitimacyAgent", "PhishingAgent"]


# ------------------------------------------------------------ consensus
def test_consensus_legitimate_campus():
    report = _report(CAMPUS)
    assert report["consensus"] == "Likely Legitimate"
    assert report["overall_risk"] == "Low"


def test_consensus_malicious_kyc():
    report = _report(FAKE_SBI)
    assert report["consensus"] in {"Likely Malicious", "Possibly Malicious"}
    assert report["overall_risk"] in {"High", "Medium"}


def test_consensus_conflict_example():
    engine = ConsensusEngine()
    reports = [
        {"name": "RecruitmentAgent", "relevance": 0.9, "confidence": 0.9,
         "risk_score": 0.08, "trust_score": 0.85, "findings": ["a"],
         "recommended_action": "", "reasoning": ""},
        {"name": "LegitimacyAgent", "relevance": 0.8, "confidence": 0.85,
         "risk_score": 0.1, "trust_score": 0.8, "findings": ["b"],
         "recommended_action": "", "reasoning": ""},
        {"name": "PhishingAgent", "relevance": 0.2, "confidence": 0.5,
         "risk_score": 0.1, "trust_score": 0.6, "findings": [],
         "recommended_action": "", "reasoning": ""},
    ]
    out = engine.reach_consensus(reports, ml_label="SPAM", ml_confidence=0.9)
    assert out["consensus"] == "Likely Legitimate (contested)"
    assert out["conflicts"]


def test_consensus_strong_alarm_floor():
    engine = ConsensusEngine()
    reports = [
        {"name": "BankingAgent", "relevance": 0.8, "confidence": 0.85,
         "risk_score": 0.88, "trust_score": 0.08, "findings": ["a"],
         "recommended_action": "", "reasoning": ""},
        {"name": "LegitimacyAgent", "relevance": 0.6, "confidence": 0.8,
         "risk_score": 0.2, "trust_score": 0.6, "findings": ["b"],
         "recommended_action": "", "reasoning": ""},
    ]
    out = engine.reach_consensus(reports, ml_label="HAM", ml_confidence=0.9)
    assert out["overall_risk"] in {"High", "Medium"}


# ------------------------------------------------------------ fusion & report
def test_evidence_fusion_buckets():
    reports = [
        {"name": "PhishingAgent", "relevance": 0.8, "confidence": 0.85,
         "risk_score": 0.9, "trust_score": 0.1, "findings": ["harvest link"],
         "recommended_action": "", "reasoning": ""},
        {"name": "LegitimacyAgent", "relevance": 0.7, "confidence": 0.8,
         "risk_score": 0.1, "trust_score": 0.85, "findings": ["formal letterhead"],
         "recommended_action": "", "reasoning": ""},
    ]
    fused = fuse_evidence(reports, {}, rag_evidence=[
        {"source": "kyc_scam.md", "score": 0.8, "category": "case_study"}])
    assert fused["negative_evidence"] and fused["positive_evidence"]
    assert fused["supporting_documents"]
    assert len(fused["agent_opinions"]) == 2


def test_report_shape_matches_rfc_example():
    report = _report(CAMPUS)
    for key in ("overall_risk", "message_type", "intent", "agents", "summary",
                "recommendation", "confidence", "evidence", "knowledge",
                "entities", "conflicts"):
        assert key in report, f"report missing {key}"
    assert len(report["agents"]) == 7
    assert report["summary"] and report["recommendation"]


# ------------------------------------------------------------ memory
def test_memory_remember_recall_feedback(tmp_path):
    mem = AgentMemory(path=tmp_path / "mem.json")
    mem.remember(CAMPUS, "Educational Announcement", "Low",
                 "Likely Legitimate", {"RecruitmentAgent": 0.9},
                 retrieval_terms=["campus drive"])
    assert mem.recall_exact(CAMPUS)["consensus"] == "Likely Legitimate"
    similar = mem.recall_similar("campus drive placement cell students")
    assert similar and similar[0]["consensus"] == "Likely Legitimate"
    assert mem.record_feedback(CAMPUS, {"verdict": "correct"}) is True
    assert mem.stats()["records"] == 1


# ------------------------------------------------------------ benchmark
def test_benchmark_no_false_positives():
    fps = [(i["id"], _report(i["text"])["consensus"])
           for i in BENCH["legitimate"]]
    bad = [(i, c) for i, c in fps if c not in ("Likely Legitimate",
                                                "Likely Legitimate (contested)")]
    assert not bad, f"consensus false positives: {bad}"


def test_benchmark_no_false_negatives():
    bad = []
    for item in BENCH["malicious"]:
        rep = _report(item["text"])
        if rep["consensus"] not in item["expected_consensus"] \
                or rep["overall_risk"] not in item["expected_risk"]:
            bad.append((item["id"], rep["consensus"], rep["overall_risk"]))
    assert not bad, f"consensus false negatives: {bad}"


def test_benchmark_per_agent_precision():
    analysis = _analysis(FAKE_SBI)
    orch = AgentOrchestrator()
    ctx = orch.build_context(analysis, text=FAKE_SBI)
    by_name = {r["name"]: r for r in orch._run_parallel(
        orch.registry.instantiate(), ctx)}
    assert by_name["PhishingAgent"]["risk_score"] >= 0.5
    assert by_name["BankingAgent"]["risk_score"] >= 0.5
    campus_analysis = _analysis(CAMPUS)
    campus_ctx = orch.build_context(campus_analysis, text=CAMPUS)
    campus_by_name = {r["name"]: r for r in orch._run_parallel(
        orch.registry.instantiate(), campus_ctx)}
    assert campus_by_name["RecruitmentAgent"]["trust_score"] >= 0.6
    assert campus_by_name["LegitimacyAgent"]["trust_score"] >= 0.6


# ------------------------------------------------------------ API + regression
def test_api_analysis_endpoint():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/analysis", json={"message": CAMPUS})
    assert response.status_code == 200
    data = response.json()
    for key in ("agent_reports", "agents", "consensus", "evidence",
                "confidence", "trust_score", "threat_score", "entities",
                "knowledge", "classification"):
        assert key in data, f"endpoint missing {key}"
    assert len(data["agent_reports"]) == 7
    assert data["consensus"] == "Likely Legitimate"


def test_regression_analyze_endpoint_untouched():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/analyze", json={"message": CAMPUS})
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] in {"SPAM", "HAM"}
    assert "risk_level" in data and "indicators" in data


def test_existing_functionality_preserved():
    analysis = _analysis(CAMPUS)
    assert analysis["classification"] in {"SPAM", "HAM"}
    assert "message_profile" in analysis
    assert "behavior_profile" in analysis
    assert "knowledge_graph" in analysis
