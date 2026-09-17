"""RFC-001 v4.0 tests: understanding engine, benchmark, FP measurement,
backward compatibility and performance."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app.understanding.entities import entity_extractor
from app.understanding.evidence import evidence_model
from app.understanding.intent_detector import intent_detector
from app.understanding.language import detect_language_info
from app.understanding.legitimacy import legitimacy_engine
from app.understanding.message_type import message_type_classifier
from app.understanding.pipeline import understanding_pipeline
from app.understanding.profile import message_profile
from app.understanding.threat import threat_engine

BENCH = json.loads((Path(__file__).resolve().parent.parent
                    / "data" / "understanding_benchmark.json").read_text(encoding="utf-8"))

RECRUIT = ("We are hiring software engineers! Walk-in interview on Monday at our "
           "Bangalore office. Apply with your resume. HR department, TechMahindra Solutions.")
EDU = ("Dear Students, University convocation ceremony will be held on 15th March. "
       "All graduating students are hereby informed to collect their gowns from the "
       "registrar office. Congratulations on your graduation!")
PHISH = ("URGENT: Your account will be BLOCKED within 2 hours! Verify your login at "
         "http://bit.ly/xyz123 and share your OTP now to avoid suspension.")


# ------------------------------------------------------------ unit: stages
def test_language_detection():
    info = detect_language_info("Hello, your OTP is 482916")
    assert info["language"] == "en"
    assert info["confidence"] > 0
    assert detect_language_info("")["language"] == "unknown"


def test_message_type_recruitment():
    out = message_type_classifier.classify(RECRUIT)
    assert out["type"] == "Recruitment"
    assert out["confidence"] >= 0.5
    assert out["evidence"]


def test_message_type_educational():
    out = message_type_classifier.classify(EDU)
    assert out["type"] == "Educational Announcement"
    assert out["confidence"] >= 0.5


def test_message_type_unknown_graceful():
    out = message_type_classifier.classify("xyzzy plugh blorp")
    assert out["type"] == "Unknown"


def test_intent_recruit():
    out = intent_detector.detect(RECRUIT)
    assert out["intent"] == "Recruit"
    assert out["confidence"] > 0
    assert out["reasoning"]


def test_intent_inform_default():
    out = intent_detector.detect(EDU)
    assert out["intent"] in {"Inform", "Congratulate", "Notify"}


def test_intent_all_16_valid():
    from app.understanding import INTENTS

    assert len(INTENTS) == 16
    for text in [RECRUIT, EDU, PHISH, "Your OTP is 482916. Valid for 10 mins."]:
        assert intent_detector.detect(text)["intent"] in INTENTS


def test_entities_structured():
    ents = entity_extractor.extract(
        "Dear Rahul Sharma, HR Manager at Infosys Ltd contact 98200 12345 or rahul@infosys.com. "
        "Interview on 12th March in Mumbai for Software Engineer role. Salary Rs.8,00,000. "
        "Track parcel at https://track.example.com/abc.")
    assert ents["total_count"] >= 6
    assert ents["people"] and ents["companies"]
    assert ents["phone_numbers"] and ents["email_addresses"]
    assert ents["money"] and ents["dates"] and ents["locations"]
    assert ents["job_titles"] and ents["urls"] and ents["domains"]


def test_entities_universities_and_govt():
    ents = entity_extractor.extract(
        "Delhi University placement cell with Ministry of Education circular. "
        "Contact the recruiter, Hiring Manager at Wipro.")
    assert ents["universities"] or ents["organizations"]
    assert ents["government_departments"]


def test_legitimacy_high_for_institutional():
    out = legitimacy_engine.analyze(EDU)
    assert out["trust_score"] >= 0.5
    names = {i["indicator"] for i in out["indicators"]}
    assert "academic_announcement" in names
    assert "no_credential_request" in names


def test_threat_high_for_phish():
    out = threat_engine.analyze(PHISH)
    assert out["threat_score"] >= 0.5
    assert "urgency" in out["families"] or "suspicious_url" in out["families"]


def test_threat_guards_toll_free_and_citation():
    govt = ("Public notice: maintenance on Sunday. Toll free helpline 1800-11-2929. "
            "As per government order 482/2026.")
    out = threat_engine.analyze(govt)
    fams = out["families"]
    assert "authority_abuse" not in fams
    assert not any(i["indicator"] == "Promotional language" and i["evidence"] == "free"
                   for i in out["indicators"])


def test_evidence_model_no_verdict():
    threat = threat_engine.analyze(PHISH)
    legit = legitimacy_engine.analyze(PHISH)
    ev = evidence_model.build(threat, legit)
    assert ev["threat_indicators"] and "classification" not in ev
    assert ev["evidence_lean"] in {"threat-leaning", "trust-leaning", "mixed"}
    assert "Threat Indicators:" in ev["summary_text"]


def test_message_profile_shape():
    full = understanding_pipeline.analyze(EDU)
    profile = full["profile"]
    for key in ("category", "intent", "threat_score", "trust_score", "entities",
                "urls", "credential_requests", "urgency", "payment_request",
                "overall_context", "risk"):
        assert key in profile
    assert profile["category"] == "Educational Announcement"
    assert profile["risk"] == "Very Low"
    assert profile["overall_context"] == "Institutional communication."


# ------------------------------------------------------------ benchmark
def _expected_list(value) -> list:
    return value if isinstance(value, list) else [value]


def test_benchmark_legitimate_low_risk():
    """False-positive slice: legitimate messages must profile Very Low/Low."""
    fps = []
    for item in BENCH["legitimate"]:
        profile = understanding_pipeline.analyze(item["text"])["profile"]
        if profile["risk"] not in item["expected_risk"]:
            fps.append((item["id"], profile["risk"]))
    assert not fps, f"false positives (legit profiled risky): {fps}"


def test_benchmark_legitimate_types_and_intents():
    misses = []
    for item in BENCH["legitimate"]:
        profile = understanding_pipeline.analyze(item["text"])["profile"]
        if profile["category"] != item["expected_type"]:
            misses.append((item["id"], "type", profile["category"]))
        if profile["intent"] not in _expected_list(item["expected_intent"]):
            misses.append((item["id"], "intent", profile["intent"]))
    assert not misses, f"benchmark misses: {misses}"


def test_benchmark_malicious_detected():
    misses = []
    for item in BENCH["malicious"]:
        profile = understanding_pipeline.analyze(item["text"])["profile"]
        if profile["risk"] not in item["expected_risk"]:
            misses.append((item["id"], "risk", profile["risk"]))
        if profile["threat_score"] < item["min_threat"]:
            misses.append((item["id"], "threat", profile["threat_score"]))
        if profile["intent"] not in _expected_list(item["expected_intent"]):
            misses.append((item["id"], "intent", profile["intent"]))
    assert not misses, f"malicious misses: {misses}"


def test_benchmark_false_positive_rate_zero():
    fps = sum(1 for item in BENCH["legitimate"]
              if understanding_pipeline.analyze(item["text"])["profile"]["risk"]
              not in ("Very Low", "Low"))
    rate = fps / len(BENCH["legitimate"])
    assert rate == 0.0, f"FP rate {rate:.2%} on legitimate slice"


# ------------------------------------------------------------ integration
def test_analysis_service_includes_understanding():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(
        AnalyzeRequest(message=EDU), store_history=False)
    # backward compatibility: legacy contract intact
    assert result["classification"] in {"SPAM", "HAM"}
    assert "risk_level" in result and "indicators" in result
    # v4 additions
    assert result["message_profile"]["category"] == "Educational Announcement"
    assert result["message_profile"]["risk"] == "Very Low"
    assert result["understanding"]["engine_version"] == "4.0.0"


def test_analysis_service_phish_still_spam_compatible():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(
        AnalyzeRequest(message=PHISH), store_history=False)
    assert result["classification"] in {"SPAM", "HAM"}
    assert result["message_profile"]["risk"] in {"Medium", "High", "Critical"}


def test_rag_still_functions():
    from app.rag.retriever import retriever

    status = retriever.status()
    assert "ready" in status and "backend" in status


def test_understanding_latency_under_300ms():
    texts = [RECRUIT, EDU, PHISH, "Your OTP is 482916. Valid for 10 mins."]
    worst = 0.0
    for text in texts:
        start = time.perf_counter()
        understanding_pipeline.analyze(text)
        worst = max(worst, (time.perf_counter() - start) * 1000.0)
    assert worst < 300.0, f"worst latency {worst:.1f}ms exceeds 300ms budget"
