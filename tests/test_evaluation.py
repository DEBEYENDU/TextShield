"""RFC-006 tests: evaluation engine, metrics, datasets, regression,
feedback, drift, reports, CLI and dashboard API."""

from __future__ import annotations

import json

import pytest

from app.evaluation import benchmark as benchmark_mod
from app.evaluation import confusion as confusion_mod
from app.evaluation import drift as drift_mod
from app.evaluation import metrics as metrics_mod
from app.evaluation import reports as reports_mod
from app.evaluation.dataset import DatasetManager, EvalSample
from app.evaluation.evaluator import EvaluationEngine
from app.evaluation.feedback import FeedbackStore
from app.evaluation.regression import check_threshold, compare_runs
from app.evaluation.versioning import fingerprint, fingerprint_id

SAMPLES = [
    EvalSample(id="t-1", message="Your OTP is 482916. Do not share it with anyone.",
               expected_label="HAM", collection="otp", difficulty="easy"),
    EvalSample(id="t-2", message="URGENT: account blocked! Verify at http://bit.ly/x now!",
               expected_label="SPAM", collection="phishing", difficulty="easy"),
    EvalSample(id="t-3", message="Team lunch tomorrow at 1 PM in the cafeteria.",
               expected_label="HAM", collection="corporate", difficulty="easy"),
    EvalSample(id="t-4", message="You WON Rs.25,00,000! Pay Rs.5,000 fee to claim today!",
               expected_label="SPAM", collection="lottery_scam", difficulty="easy"),
]


def _run_synthetic() -> dict:
    return {
        "run_id": "test-run", "fingerprint_id": "abc123",
        "records": [
            {"id": "a", "expected": "HAM", "predicted": "HAM", "confidence": 0.9,
             "message_type": "Recruitment", "collection": "recruitment",
             "threat_families": [], "spam_score": 0.1, "inference_ms": 10.0,
             "trust_score": 0.8, "threat_score": 0.1, "risk_level": "LOW"},
            {"id": "b", "expected": "HAM", "predicted": "SPAM", "confidence": 0.7,
             "message_type": "Bank Notification", "collection": "banking",
             "threat_families": [], "spam_score": 0.7, "inference_ms": 12.0,
             "trust_score": 0.5, "threat_score": 0.3, "risk_level": "MEDIUM"},
            {"id": "c", "expected": "SPAM", "predicted": "SPAM", "confidence": 0.95,
             "message_type": "Unknown", "collection": "phishing",
             "threat_families": ["credential_harvesting"], "spam_score": 0.95,
             "inference_ms": 11.0, "trust_score": 0.1, "threat_score": 0.8,
             "risk_level": "HIGH"},
            {"id": "d", "expected": "SPAM", "predicted": "HAM", "confidence": 0.6,
             "message_type": "Unknown", "collection": "bec",
             "threat_families": ["bec"], "spam_score": 0.4, "inference_ms": 9.0,
             "trust_score": 0.5, "threat_score": 0.2, "risk_level": "LOW"},
        ],
    }


# ------------------------------------------------------------ dataset
def test_dataset_loading_and_stats():
    manager = DatasetManager()
    assert len(manager.collections()) >= 10
    assert manager.stats()["total"] >= 90
    assert manager.stats()["by_label"]["HAM"] > 0
    assert manager.stats()["by_label"]["SPAM"] > 0


def test_dataset_validation():
    manager = DatasetManager()
    result = manager.validate(manager.load_all())
    assert result["valid"], result["issues"]


def test_dataset_filter_and_legacy_import():
    manager = DatasetManager()
    banking = manager.load_collection("banking")
    assert len(banking) == 12
    assert manager.filter(banking, difficulty="easy")
    legacy = manager.import_legacy_benchmarks()
    assert len(legacy) >= 40
    assert {s.expected_label for s in legacy} <= {"HAM", "SPAM"}


def test_dataset_missing_collection():
    with pytest.raises(FileNotFoundError):
        DatasetManager().load_collection("no-such-collection")


# ------------------------------------------------------------ metrics
def test_classification_metrics_known_values():
    m = metrics_mod.classification_metrics(
        ["HAM", "HAM", "SPAM", "SPAM"], ["HAM", "SPAM", "SPAM", "HAM"],
        [0.1, 0.7, 0.9, 0.4])
    assert m["accuracy"] == 0.5
    assert m["tp"] == m["tn"] == m["fp"] == m["fn"] == 1
    assert m["precision"] == m["recall"] == m["f1"] == 0.5
    assert m["false_positive_rate"] == 0.5
    assert m["false_negative_rate"] == 0.5
    assert 0.0 <= (m["roc_auc"] or 0) <= 1.0


def test_per_category_and_agent_accuracy():
    run = _run_synthetic()
    per_cat = metrics_mod.per_category_accuracy(run["records"])
    assert per_cat["banking"]["accuracy"] == 0.0
    assert per_cat["recruitment"]["accuracy"] == 1.0
    records = [dict(r, agent_opinions={
        "PhishingAgent": {"risk_score": 0.9 if r["expected"] == "SPAM" else 0.1}})
        for r in run["records"]]
    per_agent = metrics_mod.per_agent_accuracy(records)
    assert per_agent["PhishingAgent"]["accuracy"] == 1.0


def test_calibration_and_timing():
    run = _run_synthetic()
    cal = metrics_mod.confidence_calibration(run["records"])
    assert 0.0 <= cal["expected_calibration_error"] <= 1.0
    timing = metrics_mod.timing_stats(run["records"])
    assert timing["n"] == 4 and timing["avg_ms"] > 0


# ------------------------------------------------------------ confusion
def test_confusion_matrix_and_groupings():
    run = _run_synthetic()
    cm = confusion_mod.confusion_matrix(run["records"])
    assert cm["matrix"] == [[1, 1], [1, 1]]
    fps = confusion_mod.false_positives(run["records"])
    assert fps["count"] == 1
    assert "Bank Notification" in fps["by_message_type"]
    fns = confusion_mod.false_negatives(run["records"])
    assert fns["count"] == 1
    assert "bec" in fns["by_threat_family"]
    assert len(confusion_mod.error_records(run["records"])) == 2


# ------------------------------------------------------------ evaluator
def test_evaluation_engine_records(tmp_path):
    engine = EvaluationEngine(runs_dir=tmp_path / "runs")
    run = engine.evaluate(SAMPLES, run_name="unit-test-run")
    assert run["run_id"] == "unit-test-run"
    assert len(run["records"]) == 4
    record = run["records"][0]
    for key in ("expected", "predicted", "confidence", "threat_score",
                "trust_score", "threat_families", "rag_evidence",
                "llm_output", "inference_ms"):
        assert key in record, f"record missing {key}"
    assert engine.load_run("unit-test-run")["run_id"] == "unit-test-run"
    assert engine.list_runs()[0]["n_samples"] == 4


def test_versioning_fingerprint():
    fp = fingerprint()
    for key in ("model_version", "prompt_versions", "knowledge_version",
                "graph_version", "embedding_version", "weight_configuration",
                "agent_versions", "evaluation_date"):
        assert key in fp, f"fingerprint missing {key}"
    assert len(fingerprint_id(fp)) == 12
    assert fingerprint_id(fp) == fingerprint_id({**fp, "evaluation_date": "other"})


# ------------------------------------------------------------ regression
def test_regression_compare_and_gate():
    old = {"run_id": "old", "fingerprint_id": "a", "records": [
        {"id": "1", "expected": "HAM", "predicted": "HAM"},
        {"id": "2", "expected": "SPAM", "predicted": "HAM"},
        {"id": "3", "expected": "SPAM", "predicted": "SPAM"}]}
    new = {"run_id": "new", "fingerprint_id": "b", "records": [
        {"id": "1", "expected": "HAM", "predicted": "SPAM"},
        {"id": "2", "expected": "SPAM", "predicted": "SPAM"},
        {"id": "3", "expected": "SPAM", "predicted": "SPAM"}]}
    comp = compare_runs(old, new)
    assert comp["improved_count"] == 1 and comp["regressed_count"] == 1
    assert comp["shared_samples"] == 3
    assert check_threshold(comp, 0.5)["passed"] is True
    assert check_threshold(comp, 0.01)["passed"] is False


# ------------------------------------------------------------ feedback
def test_feedback_record_queue_stats(tmp_path):
    store = FeedbackStore(path=tmp_path / "feedback.json")
    store.record("suspicious msg", "false_positive", "ana", "bank alert",
                 expected="HAM", predicted="SPAM")
    store.record("missed phish", "false_negative", "ana", expected="SPAM",
                 predicted="HAM")
    assert store.stats()["total"] == 2
    queue = store.review_queue()
    assert queue[0]["verdict"] == "false_negative"  # higher priority first
    assert store.resolve(queue[0]["id"]) is True
    assert store.stats()["unresolved"] == 1
    with pytest.raises(ValueError):
        store.record("x", "bogus-verdict")
    cands = store.export_training_candidates()
    assert len(cands) == 2 and cands[0]["suggested_label"]


# ------------------------------------------------------------ drift
def test_drift_detection_flags_shifts():
    base = drift_mod.snapshot([
        {"message_type": "Bank Notification", "threat_score": 0.1,
         "confidence": 0.9, "intent": "Notify", "collection": "banking"}
        for _ in range(20)])
    same = drift_mod.snapshot([
        {"message_type": "Bank Notification", "threat_score": 0.1,
         "confidence": 0.9, "intent": "Notify", "collection": "banking"}
        for _ in range(20)])
    assert drift_mod.detect_drift(base, same)["drifted"] is False
    shifted = drift_mod.snapshot([
        {"message_type": "Unknown", "threat_score": 0.9,
         "confidence": 0.4, "intent": "Request Action", "collection": "phishing"}
        for _ in range(20)])
    result = drift_mod.detect_drift(base, shifted)
    assert result["drifted"] is True
    assert any(f["level"] == "alarm" for f in result["flags"])


# ------------------------------------------------------------ reports
def test_report_renderers():
    run = _run_synthetic()
    summary = reports_mod.summarize_run(run)
    assert summary["metrics"]["accuracy"] == 0.5
    assert summary["n_samples"] == 4
    md = reports_mod.to_markdown(run)
    assert "# Evaluation Report" in md and "False Positives" in md
    html = reports_mod.to_html(run)
    assert "<html>" in html and "Confusion matrix" in html
    csv_text = reports_mod.to_csv(run)
    assert csv_text.startswith("id,expected,predicted")
    assert len(csv_text.strip().splitlines()) == 5
    parsed = json.loads(reports_mod.to_json(run))
    assert parsed["summary"]["metrics"]["accuracy"] == 0.5


# ------------------------------------------------------------ benchmark + CLI
def test_benchmark_runner_single_collection():
    result = benchmark_mod.BenchmarkRunner().run_collection("courier")
    assert result["summary"]["n_samples"] == 8
    assert "accuracy" in result["summary"]["metrics"]


def test_cli_parsers():
    from app.evaluation.cli import benchmark, evaluate, feedback, regression, reports

    assert benchmark.build_parser().parse_args(["--dataset", "banking"]).dataset == ["banking"]
    assert evaluate.build_parser().parse_args(["--category", "fraud"]).category == "fraud"
    args = regression.build_parser().parse_args(["--old", "a", "--new", "b"])
    assert (args.old, args.new) == ("a", "b")
    assert feedback.build_parser().parse_args(["--stats"]).stats is True
    assert reports.build_parser().parse_args(["--run", "x"]).run == "x"


def test_cli_feedback_roundtrip(tmp_path, monkeypatch):
    from app.evaluation.cli import feedback as feedback_cli

    monkeypatch.chdir(tmp_path)
    assert feedback_cli.main(["--message", "m", "--verdict", "needs_review"]) == 0
    assert feedback_cli.main(["--stats"]) == 0
    assert feedback_cli.main(["--queue"]) == 0
    assert feedback_cli.main([]) == 2


# ------------------------------------------------------------ API
def test_dashboard_api_endpoints():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    assert client.get("/api/evaluation/history").status_code == 200
    assert client.get("/api/evaluation/metrics").status_code == 200
    assert client.get("/api/evaluation/confusion").status_code == 200
    assert client.get("/api/evaluation/drift").status_code == 200
    feedback = client.get("/api/evaluation/feedback").json()
    assert "stats" in feedback and "queue" in feedback
    created = client.post("/api/evaluation/feedback", json={
        "message": "api test", "verdict": "correct", "analyst": "pytest"})
    assert created.status_code == 200 and created.json()["recorded"] is True
    bad = client.post("/api/evaluation/feedback", json={
        "message": "x", "verdict": "bogus"})
    assert bad.status_code == 422
