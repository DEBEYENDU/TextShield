"""Adaptive decision engine: evidence extraction, dynamic weighting,
capped-share fusion, policy-gated verdicts.

Twelve independent sources fuse into P(spam); per-category adaptive
weights decide HOW MUCH each source counts. No source can dominate
(share cap); every source stays audible (weight floor).
"""

from __future__ import annotations

import time

from app.core.logging import get_logger
from app.decision import confidence as confidence_mod
from app.decision import calibration as calibration_mod
from app.decision.policy import DecisionPolicy
from app.decision.weighting_adaptive import SOURCES, adaptive_weights, capped_shares

logger = get_logger(__name__)

_RISK_ORDER = ["Very Low", "Low", "Medium", "High", "Critical"]


def _clip(p: float) -> float:
    return min(max(float(p), 0.01), 0.99)


def extract_sources(analysis: dict) -> dict:
    """Map the analysis payload onto 12 independent source votes.

    Each vote: {p_spam, confidence, evidence: [str]}. Missing sources
    are omitted (weight 0) rather than zero-filled.
    """
    profile = analysis.get("message_profile", {}) or {}
    understanding = analysis.get("understanding", {}) or {}
    threat = understanding.get("threat", {}) or {}
    behavior = analysis.get("behavior_profile", {}) or {}
    graph = analysis.get("knowledge_graph", {}) or {}
    votes: dict = {}

    # 1. ML classifier
    ml_label = str(analysis.get("classification", ""))
    ml_conf = float(analysis.get("confidence", 0.0) or 0.0)
    if ml_label in {"SPAM", "HAM"}:
        votes["ml"] = {"p_spam": ml_conf if ml_label == "SPAM" else 1 - ml_conf,
                       "confidence": ml_conf,
                       "evidence": [f"ML verdict {ml_label} ({ml_conf:.0%})"]}

    # 2. RAG retrieval
    rag = analysis.get("rag_evidence", []) or []
    high_risk = sum(1 for e in rag if str(e.get("category", "")) in {
        "banking_scams", "phishing", "investment_scams"})
    if rag:
        p = min(0.9, 0.3 + 0.2 * high_risk)
        votes["rag"] = {"p_spam": p, "confidence": round(min(0.9, 0.4 + 0.15 * len(rag)), 3),
                        "evidence": [f"{len(rag)} retrieved docs, {high_risk} high-risk"]}

    # 3. Knowledge graph (adjusted scores from RFC-003 reasoner)
    if graph:
        p = float(graph.get("adjusted_threat", profile.get("threat_score", 0.5)) or 0.0)
        campaigns = graph.get("campaign_matches", [])
        votes["graph"] = {"p_spam": _clip(p),
                          "confidence": 0.7 if campaigns else 0.5,
                          "evidence": ([f"campaign match: {c}" for c in campaigns[:2]]
                                       or ["no campaign match"])}

    # 4. Threat intelligence (indicators + URLs)
    indicators = analysis.get("indicators", []) or []
    urls = analysis.get("urls", []) or []
    threat_score = float(profile.get("threat_score", 0.0) or 0.0)
    if indicators or urls or threat_score > 0:
        high = sum(1 for i in indicators if i.get("severity") == "high")
        votes["threat_intel"] = {
            "p_spam": _clip(max(threat_score, min(0.9, 0.25 + 0.2 * high))),
            "confidence": round(min(0.9, 0.4 + 0.15 * (len(indicators) + len(urls))), 3),
            "evidence": [f"{len(indicators)} indicators ({high} high), {len(urls)} urls"]}

    # 5. Behavior engine
    manip = float(behavior.get("manipulation_score", 0.0) or 0.0)
    urg = (behavior.get("urgency", {}) or {}).get("level", "Low")
    if behavior:
        p = _clip(manip * 0.8 + (0.25 if urg in {"High", "Critical"} else 0.0))
        votes["behavior"] = {"p_spam": p, "confidence": 0.65,
                             "evidence": [f"manipulation {behavior.get('manipulation_level', '?')} "
                                          f"({manip}), urgency {urg}"]}

    # 6. Intent engine (malicious request intents)
    intent_label = str((analysis.get("intent", {}) or {}).get("label", "other"))
    if intent_label not in {"", "other", "engagement"}:
        from app.ml.intent import is_malicious_intent

        malicious = is_malicious_intent(intent_label)
        votes["intent"] = {"p_spam": 0.8 if malicious else 0.3,
                           "confidence": 0.7 if malicious else 0.4,
                           "evidence": [f"sender intent: {intent_label}"]}

    # 7. Message type (Unknown + threat is itself a weak signal)
    category = str(profile.get("category", "Unknown"))
    if category == "Unknown" and threat_score >= 0.3:
        votes["message_type"] = {"p_spam": 0.6, "confidence": 0.4,
                                 "evidence": ["unrecognized type in threat context"]}
    elif category != "Unknown":
        votes["message_type"] = {"p_spam": _clip(threat_score),
                                 "confidence": float(profile.get("category_confidence", 0.5) or 0.5),
                                 "evidence": [f"type {category}"]}

    # 8. Entity analysis (credential/URL-heavy messages)
    entities = understanding.get("entities", {}) or {}
    n_urls = len(entities.get("urls", []))
    n_cred = sum(1 for i in threat.get("indicators", [])
                 if "credential" in str(i.get("indicator", "")).lower())
    if n_urls or n_cred or entities.get("total_count", 0):
        votes["entities"] = {"p_spam": _clip(0.3 + 0.2 * n_urls + 0.25 * n_cred),
                             "confidence": 0.55,
                             "evidence": [f"{n_urls} urls, {n_cred} credential requests"]}

    # 9. LLM reasoning (weak signal: source + agreement with ML)
    expl_source = str(analysis.get("explanation_source", "template"))
    if expl_source:
        votes["llm"] = {"p_spam": _clip(threat_score if expl_source == "llm" else 0.4),
                        "confidence": 0.6 if expl_source == "llm" else 0.3,
                        "evidence": [f"explanation source: {expl_source}"]}

    # 10. Multi-agent consensus
    consensus = ((analysis.get("agent_report", {}) or {}).get("consensus")
                 or (analysis.get("consensus") if isinstance(analysis.get("consensus"), str) else None))
    agent_risk = None
    agent_block = analysis.get("agent_report", {}) or {}
    if isinstance(agent_block.get("risk_score"), (int, float)):
        agent_risk = float(agent_block["risk_score"])
    if consensus or agent_risk is not None:
        p = _clip(agent_risk if agent_risk is not None else
                  (0.75 if "Malicious" in str(consensus)
                   else 0.2 if "Legitimate" in str(consensus) else 0.5))
        votes["agents"] = {"p_spam": p, "confidence": 0.7,
                           "evidence": [f"consensus: {consensus or 'n/a'}"]}

    # 11. Historical similarity (agent memory recall)
    similar = ((analysis.get("agent_report", {}) or {}).get("similar_past")
               or analysis.get("similar_past") or [])
    if similar:
        spammy = sum(1 for s in similar if "Malicious" in str(s.get("consensus", "")))
        votes["history"] = {"p_spam": round(spammy / len(similar), 3),
                            "confidence": 0.5,
                            "evidence": [f"{len(similar)} similar past messages"]}

    # 12. Legitimacy (trust evidence pulls toward HAM)
    trust = float(profile.get("trust_score", 0.5) or 0.5)
    legitimacy = understanding.get("legitimacy", {}) or {}
    if legitimacy or trust != 0.5:
        votes["legitimacy"] = {"p_spam": _clip(1 - trust), "confidence": 0.6,
                               "evidence": [f"trust score {trust:.2f}"]}
    return votes


class AdaptiveEngine:
    """Fuse adaptive-weighted evidence into a policy-gated decision."""

    def __init__(self, calibrator=None):
        self.calibrator = calibrator or calibration_mod.calibrator

    def decide(self, analysis: dict, policy: DecisionPolicy,
               category: str | None = None) -> dict:
        started = time.perf_counter()
        category = category or str((analysis.get("message_profile", {}) or {}).get("category", "Unknown"))
        votes = extract_sources(analysis)
        if not votes:
            return {"decision": "HAM", "p_spam": 0.5, "confidence": 0.0,
                    "risk": "Low", "policy": policy.name, "category": category,
                    "sources": {}, "weights": {}, "shares": {},
                    "contributions": [], "uncertainty": 1.0,
                    "latency_ms": 0.0}
        confidences = {s: v["confidence"] for s, v in votes.items()}
        weights = adaptive_weights(category, policy, confidences)
        weights = {s: weights.get(s, 0.8) for s in votes}
        shares = capped_shares(weights)
        p_spam = round(sum(votes[s]["p_spam"] * shares[s] for s in votes), 4)
        contributions = sorted(
            [{"source": s, "p_spam": votes[s]["p_spam"], "weight": weights[s],
              "share": shares[s],
              "contribution": round((votes[s]["p_spam"] - 0.5) * shares[s], 4),
              "evidence": votes[s]["evidence"]} for s in votes],
            key=lambda c: -abs(c["contribution"]))
        p_list = [votes[s]["p_spam"] for s in votes]
        conf = confidence_mod.context_confidence(
            p_list, len(votes),
            calibrated_p=self.calibrator.calibrate(
                confidence_mod.context_confidence(p_list, len(votes))["raw_confidence"]))
        uncertainty = round(1 - conf["calibrated_confidence"], 3)
        label = "SPAM" if p_spam >= policy.spam_threshold else "HAM"
        risk = ("High" if p_spam >= policy.high_risk_threshold
                else "Medium" if p_spam >= policy.spam_threshold
                else "Low" if p_spam >= 0.2 else "Very Low")
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return {"decision": label, "p_spam": p_spam,
                "confidence": conf["calibrated_confidence"],
                "raw_confidence": conf["raw_confidence"],
                "agreement": conf["agreement"], "coverage": conf["coverage"],
                "risk": risk, "policy": policy.name, "category": category,
                "sources": {s: {"p_spam": votes[s]["p_spam"],
                                "confidence": votes[s]["confidence"]} for s in votes},
                "weights": weights, "shares": shares,
                "contributions": contributions, "uncertainty": uncertainty,
                "n_sources": len(votes), "latency_ms": elapsed_ms}


adaptive_engine = AdaptiveEngine()
