"""Human review routing: decide when a message needs analyst eyes.

Routes to review on evidence conflict, low confidence, high-risk/low-
certainty, unknown type or organization, and novel attack patterns.
Sensitivity scales with the active policy; enterprise can force review
on conflict or medium+ risk.
"""

from __future__ import annotations

_RISK_RANK = {"Very Low": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def route_for_review(decision: dict, analysis: dict, policy) -> dict:
    """Return {needs_review, reasons, priority} for a decision."""
    reasons: list[str] = []
    sensitivity = float(getattr(policy, "review_sensitivity", 1.0))
    review_threshold = float(getattr(policy, "review_threshold", 0.35))

    conflicts = _collect_conflicts(decision, analysis)
    # conflicts route only genuine toss-ups with convicted dissenters;
    # lopsided verdicts with a lone weak dissenter are decided, not conflicted
    p_spam_early = float(decision.get("p_spam", 0.5))
    convicted = [c for c in decision.get("contributions", [])
                 if abs(c.get("p_spam", 0.5) - 0.5) * 2
                 * (0.5 + decision.get("sources", {}).get(c["source"], {}).get("confidence", 0.5)) > 0.5]
    spam_side = any(c["p_spam"] >= 0.6 for c in convicted)
    ham_side = any(c["p_spam"] <= 0.4 for c in convicted)
    if conflicts and spam_side and ham_side and abs(p_spam_early - 0.5) < 0.15:
        reasons.append(f"evidence conflict: {conflicts[0]}")
    confidence = float(decision.get("confidence", 0.0) or 0.0)
    if confidence < float(getattr(policy, "min_review_confidence", 0.65)):
        reasons.append(f"confidence {confidence:.0%} below "
                       f"{getattr(policy, 'min_review_confidence', 0.65):.0%}")
    risk = str(decision.get("risk", "Low"))
    if risk in {"High", "Critical"} and decision.get("uncertainty", 0) > 0.4:
        reasons.append(f"{risk} risk with high uncertainty")
    # model-evidence disagreement: fusion and ML pull opposite directions
    ml_p = (decision.get("sources", {}) or {}).get("ml", {}).get("p_spam")
    fusion_p = decision.get("fusion_p_spam")
    if ml_p is not None and fusion_p is not None \
            and abs(ml_p - fusion_p) > 0.4:
        reasons.append(f"model ({ml_p:.2f}) disagrees with fused evidence ({fusion_p:.2f})")
    category = str(decision.get("category", "Unknown"))
    threat_level = float((analysis.get("message_profile", {}) or {}).get("threat_score", 0.0) or 0.0)
    if category == "Unknown" and threat_level >= 0.5:
        reasons.append("unknown message type with high threat")
    graph = analysis.get("knowledge_graph", {}) or {}
    if graph.get("unknown_domains"):
        reasons.append(f"unknown organization/domain: "
                       f"{', '.join(graph['unknown_domains'][:2])}")
    if _novel_pattern(decision, analysis):
        reasons.append("novel phishing technique or scam pattern")
    p_spam = float(decision.get("p_spam", 0.5))
    # close call with low confidence: uncertain AND near the boundary.
    # Confident verdicts (even off-center ones) do not route on this rule.
    _band = review_threshold * 0.5 * sensitivity
    if confidence < float(getattr(policy, "min_review_confidence", 0.65)) \
            and abs(p_spam - 0.5) < _band:
        reasons.append("uncertain verdict near decision boundary")

    needs_review = bool(reasons)
    if getattr(policy, "force_review_on_conflict", False) and conflicts:
        needs_review = True
    min_risk = str(getattr(policy, "force_review_min_risk", "Critical"))
    if getattr(policy, "force_review_on_conflict", False) and \
            _RISK_RANK.get(risk, 0) >= _RISK_RANK.get(min_risk, 3):
        if f"enterprise policy: {risk} risk requires review" not in reasons:
            reasons.append(f"enterprise policy: {risk} risk requires review")
        needs_review = True
    if risk in {"High", "Critical"}:
        priority = "high"
    elif reasons:
        priority = "medium"
    else:
        priority = "none"
    return {"needs_review": needs_review, "reasons": reasons[:6],
            "priority": priority, "policy": getattr(policy, "name", "balanced")}


def _collect_conflicts(decision: dict, analysis: dict) -> list[str]:
    conflicts = []
    contributions = decision.get("contributions", [])
    spam_side = [c["source"] for c in contributions
                 if c["p_spam"] >= 0.65 and c["share"] >= 0.08]
    ham_side = [c["source"] for c in contributions
                if c["p_spam"] <= 0.35 and c["share"] >= 0.08]
    if spam_side and ham_side:
        conflicts.append(f"{'/'.join(spam_side[:2])} vs {'/'.join(ham_side[:2])}")
    agent_block = analysis.get("agent_report", {}) or {}
    for conflict in agent_block.get("conflicts", []) or []:
        conflicts.append(f"agents: {conflict[:80]}")
    kg_conflicts = (analysis.get("knowledge_graph", {}) or {}).get("reasons", [])
    if decision.get("decision") == "HAM" and any("campaign" in str(r).lower() for r in kg_conflicts):
        conflicts.append("graph links entities to a known campaign")
    return conflicts


def _novel_pattern(decision: dict, analysis: dict) -> bool:
    """Heuristic novelty: elevated threat with no known campaign match."""
    profile = analysis.get("message_profile", {}) or {}
    if float(profile.get("threat_score", 0.0) or 0.0) < 0.45:
        return False
    graph = analysis.get("knowledge_graph", {}) or {}
    if graph.get("campaign_matches"):
        return False
    # elevated threat with no known campaign: potentially novel — but only
    # route when the decision itself is not already confident spam
    return float(decision.get("p_spam", 0.0) or 0.0) < 0.7
