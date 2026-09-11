"""RFC-007 tests: adaptive weighting, policies, fusion, calibration,
routing, explanation, APIs and benchmark regression guards."""

from __future__ import annotations

import pytest

from app.decision.adaptive_engine import adaptive_engine, extract_sources
from app.decision.calibration import Calibrator
from app.decision.confidence import agreement_score, context_confidence
from app.decision.explanation import build_explanation
from app.decision.policy import POLICY_NAMES, get_policy, load_policies
from app.decision.review import ReviewQueue
from app.decision.routing import route_for_review
from app.decision.weighting_adaptive import adaptive_weights, capped_shares
from app.evaluation.feedback import FeedbackStore

CAMPUS = ("Dear Students, Technolearn placement cell announces a campus drive "
          "on 12th March. Register via the Google Form link. No fees.")
FAKE_SBI = ("URGENT: State Bank of India KYC suspended! Verify your login at "
            "http://bit.ly/sbi-kyc now and share OTP within 2 hours.")


def _analysis(text: str) -> dict:
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    return analysis_service.analyze(AnalyzeRequest(message=text),
                                    store_history=False)


def _decide(text: str, policy_name: str = "balanced") -> tuple[dict, dict]:
    analysis = _analysis(text)
    return adaptive_engine.decide(analysis, get_policy(policy_name)), analysis


# ------------------------------------------------------------ policies
def test_policies_load_from_config():
    bundle = load_policies()
    assert set(bundle["policies"]) >= {"conservative", "balanced", "aggressive",
                                       "enterprise", "research"}
    assert "Recruitment" in bundle["category_profiles"]
    assert "fusion" in bundle


def test_policy_switching_changes_thresholds():
    conservative = get_policy("conservative")
    aggressive = get_policy("aggressive")
    assert conservative.spam_threshold < aggressive.spam_threshold
    assert conservative.review_sensitivity > aggressive.review_sensitivity


def test_custom_policy_overrides():
    custom = get_policy("custom", overrides={"spam_threshold": 0.42})
    assert custom.name == "custom"
    assert custom.spam_threshold == 0.42
    with pytest.raises(ValueError):
        get_policy("no-such-policy")


# ------------------------------------------------------------ adaptive weighting
def test_weights_adapt_per_category():
    policy = get_policy("balanced")
    rec = adaptive_weights("Recruitment", policy)
    bank = adaptive_weights("Bank Notification", policy)
    assert rec["agents"] > bank["agents"]
    assert rec["legitimacy"] > bank["legitimacy"]
    assert bank["threat_intel"] > rec["threat_intel"]
    assert all(0.4 <= w <= 1.8 for w in rec.values())


def test_capped_shares_prevent_dominance():
    shares = capped_shares({"a": 10.0, "b": 1.0, "c": 1.0}, max_share=0.35)
    assert max(shares.values()) <= 0.35 + 1e-9
    assert abs(sum(shares.values()) - 1.0) < 1e-6


# ------------------------------------------------------------ fusion & decision
def test_campus_decision_ham_with_weights():
    decision, _ = _decide(CAMPUS)
    assert decision["decision"] == "HAM"
    assert decision["p_spam"] < 0.5
    assert decision["policy"] == "balanced"
    assert decision["n_sources"] >= 3
    top = decision["contributions"][0]
    assert {"source", "share", "contribution", "evidence"} <= set(top)


def test_phish_decision_spam():
    decision, _ = _decide(FAKE_SBI)
    assert decision["decision"] == "SPAM"
    assert decision["p_spam"] >= 0.5
    assert decision["risk"] in {"High", "Critical", "Medium"}


def test_evidence_sources_independent():
    analysis = _analysis(FAKE_SBI)
    votes = extract_sources(analysis)
    assert "ml" in votes and "threat_intel" in votes
    assert all(0.0 <= v["p_spam"] <= 1.0 for v in votes.values())
    assert all(v["evidence"] for v in votes.values())


# ------------------------------------------------------------ confidence & calibration
def test_confidence_agreement():
    assert agreement_score([0.9, 0.85, 0.92]) > agreement_score([0.9, 0.1, 0.5])
    assert agreement_score([]) == 0.0
    out = context_confidence([0.8, 0.7], 2)
    assert 0.0 <= out["raw_confidence"] <= 1.0
    assert out["coverage"] > 0


def test_calibrator_learns_and_fallbacks():
    records = [{"expected": "SPAM", "predicted": "SPAM", "confidence": 0.9},
               {"expected": "HAM", "predicted": "SPAM", "confidence": 0.9},
               {"expected": "HAM", "predicted": "HAM", "confidence": 0.2}]
    cal = Calibrator.from_run_records(records, n_bins=2)
    assert 0.0 <= cal.calibrate(0.95) <= 1.0
    assert 0.0 <= cal.expected_calibration_error(records) <= 1.0
    fallback = Calibrator.from_latest_run(runs_dir="/nonexistent-dir")
    assert fallback.calibrate(0.8) > 0


# ------------------------------------------------------------ routing & review
def test_routing_triggers_on_conflict_and_novelty():
    decision, analysis = _decide(FAKE_SBI)
    routing = route_for_review(decision, analysis, get_policy("balanced"))
    assert "needs_review" in routing and "priority" in routing
    calm, _ = _decide(CAMPUS)
    calm_routing = route_for_review(calm, _analysis(CAMPUS), get_policy("balanced"))
    assert isinstance(calm_routing["needs_review"], bool)


def test_review_queue_lifecycle(tmp_path):
    queue = ReviewQueue(FeedbackStore(path=tmp_path / "feedback.json"))
    item = queue.submit("suspicious message", ["low confidence"], "high")
    assert queue.claim(item["id"], "ana-1") is True
    assert queue.resolve(item["id"], "false_positive", "ana-1", "bank alert") is True
    assert queue.stats()["total"] == 1
    with pytest.raises(ValueError):
        queue.resolve(item["id"], "bogus")


# ------------------------------------------------------------ explanation
def test_explanation_shape_matches_rfc():
    decision, analysis = _decide(CAMPUS)
    expl = build_explanation(decision, analysis)
    for key in ("final_risk", "decision", "reasons", "confidence",
                "policy", "top_contributors", "uncertainty"):
        assert key in expl, f"explanation missing {key}"
    assert expl["reasons"]
    assert expl["decision"] == "HAM"


# ------------------------------------------------------------ APIs
def test_decision_apis():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    decision = client.post("/api/decision", json={"message": CAMPUS}).json()
    assert decision["decision"] == "HAM"
    assert "confidence" in decision and "policy" in decision
    assert "review" in decision and "evidence_summary" in decision
    evidence = client.post("/api/evidence", json={"message": CAMPUS}).json()
    assert evidence["contributions"] and evidence["weights"]
    assert abs(sum(evidence["shares"].values()) - 1.0) < 0.01
    confidence = client.post("/api/confidence", json={"message": CAMPUS}).json()
    assert {"confidence", "agreement", "coverage", "uncertainty"} <= set(confidence)
    review = client.post("/api/review", json={"message": CAMPUS}).json()
    assert "routing" in review and "queue" in review
    assert client.get("/api/review").status_code == 200
    policies = client.get("/api/decision/policies").json()
    assert set(policies["policies"]) >= {"balanced", "conservative", "aggressive"}
    claim = client.post("/api/review/nonexistent-id/claim")
    assert claim.status_code == 200 and claim.json()["claimed"] is False
    resolve = client.post("/api/review/nonexistent-id/resolve",
                          json={"verdict": "false_positive"})
    assert resolve.status_code == 200


# ------------------------------------------------------------ benchmarks
def test_benchmark_accuracy_and_fp_reduction():
    from app.evaluation.dataset import DatasetManager

    policy = get_policy("balanced")
    samples = DatasetManager().load_all()
    ok = fp = fn = 0
    ml_fp = 0
    for sample in samples:
        analysis = _analysis(sample.message)
        decision = adaptive_engine.decide(analysis, policy)["decision"]
        if decision == sample.expected_label:
            ok += 1
        elif sample.expected_label == "HAM":
            fp += 1
        else:
            fn += 1
        if analysis["classification"] == "SPAM" and sample.expected_label == "HAM":
            ml_fp += 1
    n = len(samples)
    assert ok / n >= 0.85, f"decision accuracy {ok}/{n} below 0.85"
    assert fp <= ml_fp, f"decision FP {fp} worse than ML FP {ml_fp}"
    assert fn <= 3, f"too many false negatives: {fn}"


def test_policy_characters():
    from app.evaluation.dataset import DatasetManager

    samples = DatasetManager().load_all()[:30]
    results = {}
    for name in ("conservative", "aggressive"):
        policy = get_policy(name)
        fp = fn = 0
        for sample in samples:
            decision = adaptive_engine.decide(
                _analysis(sample.message), policy)["decision"]
            if decision != sample.expected_label:
                if sample.expected_label == "HAM":
                    fp += 1
                else:
                    fn += 1
        results[name] = (fp, fn)
    assert results["conservative"][1] <= results["aggressive"][1]  # fewer FN
    assert results["aggressive"][0] <= results["conservative"][0]  # fewer FP


def test_regression_analyze_endpoint_untouched():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/analyze", json={"message": CAMPUS})
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] in {"SPAM", "HAM"}
    assert "risk_level" in data and "indicators" in data
