"""RFC-004 tests: behavioral engine units, benchmark (FP/FN/accuracy),
integration (trust, RAG, graph, LLM prompt) and regression guards."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app.behavior.analyzer import behavioral_analyzer, behavior_context_block
from app.behavior.authority import AuthorityDetector
from app.behavior.conversation import ConversationAnalyzer
from app.behavior.emotion import EmotionAnalyzer
from app.behavior.linguistic import LinguisticAnalyzer
from app.behavior.manipulation import ManipulationAnalyzer
from app.behavior.persuasion import PersuasionAnalyzer
from app.behavior.profile import BehaviorProfileBuilder, StyleClassifier
from app.behavior.psychology import PsychologyDetector
from app.behavior.urgency import UrgencyDetector

BENCH = json.loads((Path(__file__).resolve().parent.parent
                    / "data" / "behavior_benchmark.json").read_text(encoding="utf-8"))

CEO = ("This is the CEO. Confidential acquisition underway, keep this between us. "
       "Transfer Rs.5,00,000 to the vendor immediately. I am in a meeting, do not call.")
KYC_PHISH = ("URGENT: SBI KYC suspended! Verify login at http://bit.ly/x and share OTP "
             "within 2 hours or account blocked!")
RECRUIT = ("We are hiring software engineers! Walk-in interview Monday at Bangalore "
           "office. Apply with resume. HR department.")
OTP = "Your OTP is 482916. Valid for 10 mins. Do not share with anyone."


# ------------------------------------------------------------ unit tests
def test_authority_detection_ceo_fraud():
    out = AuthorityDetector().detect(CEO)
    assert "CEO Fraud" in out["names"]
    assert out["personas"][0]["confidence"] >= 0.5
    assert out["personas"][0]["evidence"]


def test_authority_detection_tech_support():
    out = AuthorityDetector().detect(
        "MICROSOFT SECURITY ALERT: virus detected! Call our technician now!")
    assert "Tech Support" in out["names"]


def test_authority_detection_benign_empty():
    out = AuthorityDetector().detect("Reminder: appointment tomorrow at 10 AM.")
    assert out["count"] == 0


def test_fear_detection():
    out = PsychologyDetector().detect(KYC_PHISH)
    assert "Fear" in out["names"]
    assert "Urgency" in out["names"]


def test_psychology_benign_quiet():
    out = PsychologyDetector().detect(RECRUIT)
    assert "Fear" not in out["names"]
    assert "Threat" not in out["names"]


def test_urgency_detection_critical():
    out = UrgencyDetector().detect(KYC_PHISH)
    assert out["level"] == "Critical"
    assert out["urgency_score"] >= 0.7
    assert len(out["evidence"]) >= 2


def test_urgency_discounts_otp_window():
    out = UrgencyDetector().detect(OTP)
    assert out["level"] == "Low"


def test_emotion_extraction():
    out = EmotionAnalyzer().analyze(KYC_PHISH)
    assert out["dominant"] in {"Fear", "Panic", "Urgency", "Pressure"}
    assert out["weaponized_score"] > 0
    benign = EmotionAnalyzer().analyze(RECRUIT)
    assert benign["weaponized_score"] < out["weaponized_score"]


def test_emotion_is_not_sentiment():
    out = EmotionAnalyzer().analyze(
        "Congratulations! You won the lucky draw, claim now, offer ends tonight!")
    assert "Excitement" in out["emotion_profile"] or "Greed" in out["emotion_profile"]


def test_communication_style():
    bundle = {"linguistic": {"professional_tone": "Professional",
                             "formatting": "Consistent",
                             "grammar_quality": "Good",
                             "sentence_complexity": "Moderate",
                             "abuse_signals": []},
              "conversation": {"flow": "Informational", "pressure_flow": "Low",
                               "question_count": 0},
              "manipulation": {"level": "Minimal"},
              "emotion": {"weaponized_score": 0.0, "emotion_profile": {}},
              "persuasion": {"names": []},
              "message_type": "Recruitment"}
    assert StyleClassifier().classify(bundle)["style"] in {
        "Corporate", "Professional", "Formal"}


def test_behavior_profile_shape():
    result = behavioral_analyzer.analyze(RECRUIT, message_type="Recruitment")
    profile = result["behavior_profile"]
    for key in ("communication_style", "psychological_triggers",
                "social_engineering", "emotion_profile", "urgency",
                "persuasion", "overall_behavior", "confidence"):
        assert key in profile
    assert profile["manipulation_level"] in {"Minimal", "Low"}
    assert result["latency_ms"] < 300.0


def test_manipulation_composer_levels():
    manip = ManipulationAnalyzer().analyze(
        {"names": ["Fear", "Urgency"],
         "techniques": [{"technique": "Fear", "score": 2.0},
                        {"technique": "Urgency", "score": 1.5}]},
        {"names": ["Threat"],
         "techniques": [{"technique": "Threat", "score": 1.8}]},
        {"names": ["CEO Fraud"],
         "personas": [{"persona": "CEO Fraud", "score": 2.0}]},
        {"urgency_score": 0.8})
    assert manip["level"] == "High"
    calm = ManipulationAnalyzer().analyze(
        {"names": [], "techniques": []}, {"names": [], "techniques": []},
        {"names": [], "personas": []}, {"urgency_score": 0.0})
    assert calm["level"] == "Minimal"


def test_linguistic_abuse_signals():
    out = LinguisticAnalyzer().analyze("WIN NOW!!! CLICK HERE!!! FREE MONEY!!!")
    assert out["abuse_signals"]
    assert out["professional_tone"] == "Aggressive"
    good = LinguisticAnalyzer().analyze(
        "Dear Team,\nPlease find the agenda attached.\nBest regards,\nHR Team")
    assert good["formatting"] == "Consistent"
    assert good["grammar_quality"] in {"Good", "Fair"}


def test_conversation_flow():
    out = ConversationAnalyzer().analyze(
        "Pay now! Send OTP! No further reminders! Click here!")
    assert out["flow"] == "Abrupt Demand"
    assert out["pressure_flow"] == "High"
    assert out["call_to_actions"]


# ------------------------------------------------------------ benchmark
def test_benchmark_legitimate_no_false_positives():
    fps = []
    for item in BENCH["legitimate"]:
        p = behavioral_analyzer.analyze(
            item["text"],
            message_type=item.get("message_type", "Unknown"))["behavior_profile"]
        if p["communication_style"] not in item["expected_style"]:
            fps.append((item["id"], "style", p["communication_style"]))
        if p["manipulation_level"] not in item["expected_manipulation"]:
            fps.append((item["id"], "manip", p["manipulation_level"]))
        if p["urgency"]["level"] not in item["expected_urgency"]:
            fps.append((item["id"], "urgency", p["urgency"]["level"]))
    assert not fps, f"behavioral false positives: {fps}"


def test_benchmark_malicious_detected():
    fns = []
    for item in BENCH["malicious"]:
        p = behavioral_analyzer.analyze(item["text"])["behavior_profile"]
        if p["manipulation_level"] not in item["expected_manipulation"]:
            fns.append((item["id"], "manip", p["manipulation_level"]))
        if p["urgency"]["level"] not in item["expected_urgency"]:
            fns.append((item["id"], "urgency", p["urgency"]["level"]))
        if len(p["psychological_triggers"]) < item["min_triggers"]:
            fns.append((item["id"], "triggers", p["psychological_triggers"]))
        for persona in item.get("expected_personas", []):
            if persona not in p["social_engineering"]:
                fns.append((item["id"], "persona", p["social_engineering"]))
    assert not fns, f"behavioral false negatives: {fns}"


def test_benchmark_accuracy_report():
    total = len(BENCH["legitimate"]) + len(BENCH["malicious"])
    correct = 0
    for item in BENCH["legitimate"]:
        p = behavioral_analyzer.analyze(
            item["text"],
            message_type=item.get("message_type", "Unknown"))["behavior_profile"]
        if (p["communication_style"] in item["expected_style"]
                and p["manipulation_level"] in item["expected_manipulation"]):
            correct += 1
    for item in BENCH["malicious"]:
        p = behavioral_analyzer.analyze(item["text"])["behavior_profile"]
        if (p["manipulation_level"] in item["expected_manipulation"]
                and len(p["psychological_triggers"]) >= item["min_triggers"]):
            correct += 1
    assert correct / total >= 0.9, f"behavior accuracy {correct}/{total}"


# ------------------------------------------------------------ integration
def test_trust_integration_deltas():
    calm = behavioral_analyzer.analyze(RECRUIT, message_type="Recruitment")
    assert calm["trust_adjustment"] >= 0
    assert calm["threat_adjustment"] == 0.0
    hostile = behavioral_analyzer.analyze(CEO)
    assert hostile["threat_adjustment"] > 0
    assert hostile["trust_adjustment"] == 0.0
    for result in (calm, hostile):
        assert -0.3 <= result["trust_adjustment"] <= 0.3
        assert -0.3 <= result["threat_adjustment"] <= 0.3


def test_rag_integration_terms():
    result = behavioral_analyzer.analyze(CEO)
    assert "CEO fraud" in result["rag_terms"]
    assert result["rag_terms"]  # non-empty for hostile
    calm_terms = behavioral_analyzer.analyze(RECRUIT)["rag_terms"]
    assert isinstance(calm_terms, list)


def test_graph_integration_edges():
    result = behavioral_analyzer.analyze(CEO)
    edges = result["graph_edges"]
    assert edges
    uses = [e for e in edges if e["rel"] == "Uses"]
    assert uses and uses[0]["src_label"] == "CEO Fraud"
    assert all(e["dst_type"] == "ATTACK_PATTERN" for e in uses)


def test_llm_context_block():
    block = behavior_context_block(behavioral_analyzer.analyze(CEO))
    for line in ("Communication Style:", "Psychological Triggers:",
                 "Claimed Persona:", "Urgency:", "Manipulation:",
                 "Overall Behavior:"):
        assert line in block
    assert "CEO Fraud" in block


def test_analysis_includes_behavior():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(AnalyzeRequest(message=CEO),
                                      store_history=False)
    bp = result["behavior_profile"]
    assert bp["manipulation_level"] == "High"
    assert "CEO Fraud" in bp["social_engineering"]
    assert result["behavior"]["threat_adjustment"] > 0
    # legacy contract untouched
    assert result["classification"] in {"SPAM", "HAM"}
    assert "risk_level" in result and "indicators" in result


def test_analysis_benign_behavior_quiet():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(AnalyzeRequest(message=RECRUIT),
                                      store_history=False)
    assert result["behavior_profile"]["manipulation_level"] in {"Minimal", "Low"}


def test_generator_prompt_contains_behavior():
    from app.rag.generator import _user_prompt

    prompt = _user_prompt({"message": "hi",
                           "behavior_context": "BEHAVIORAL ANALYSIS (influence"})
    assert "BEHAVIORAL ANALYSIS" in prompt


# ------------------------------------------------------------ regression
def test_regression_otp_stays_calm():
    p = behavioral_analyzer.analyze(
        OTP, message_type="OTP / Authentication")["behavior_profile"]
    assert p["manipulation_level"] in {"Minimal", "Low"}
    assert p["urgency"]["level"] in {"Low", "Medium"}
    assert p["social_engineering"] == []


def test_regression_govt_circular_not_coercive():
    p = behavioral_analyzer.analyze(
        "Public notice: water maintenance Sunday. Toll free helpline 1800-11-2929.",
        message_type="Government Advisory")["behavior_profile"]
    assert p["manipulation_level"] in {"Minimal", "Low"}
    assert "Fear" not in p["psychological_triggers"]


def test_never_raises_on_garbage():
    for text in ("", "   ", "!!!", "x" * 5000, "\x00\x01\x02"):
        out = behavioral_analyzer.analyze(text)
        assert "behavior_profile" in out


def test_latency_budget():
    worst = 0.0
    for item in BENCH["legitimate"] + BENCH["malicious"]:
        start = time.perf_counter()
        behavioral_analyzer.analyze(item["text"])
        worst = max(worst, (time.perf_counter() - start) * 1000.0)
    assert worst < 300.0, f"worst {worst:.1f}ms over budget"
