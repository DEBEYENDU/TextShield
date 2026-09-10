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
    if conflicts:
        reasons.append(f"evidence conflict: {conflicts[0]}")
    confidence = float(decision.get("confidence", 0.0) or 0.0)
    if confidence < float(getattr(policy, "min_review_confidence", 0.65)):
        reasons.append(f"confidence {confidence:.0%} below "
                       f"{getattr(policy, 'min_review_confidence', 0.65):.0%}")
    risk = str(decision.get("risk", "Low"))
    if risk in {"High", "Critical"} and decision.get("uncertainty", 0) > 0.3:
        reasons.append(f"{risk} risk with high uncertainty")
    category = str(decision.get("category", "Unknown"))
    if category == "Unknown":
        reasons.append("unknown message type")
    graph = analysis.get("knowledge_graph", {}) or {}
    if graph.get("unknown_domains"):
        reasons.append(f"unknown organization/domain: "
                       f"{', '.join(graph['unknown_domains'][:2])}")
    if _novel_pattern(decision, analysis):
        reasons.append("novel phishing technique or scam pattern")
    p_spam = float(decision.get("p_spam", 0.5))
    if abs(p_spam - 0.5) < review_threshold / max(sensitivity, 0.1):
        reasons.append("verdict near decision boundary")

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
    """Heuristic novelty: high-threat families never seen in the graph store."""
    try:
        from app.knowledge_graph.graph_store import open_graph_store

        known_families = set()
        for node in open_graph_store().load().nodes.values():
            if node.type in {"CAMPAIGN", "SCAM", "ATTACK_PATTERN"}:
                known_families.add(node.normalized)
        threat = (analysis.get("understanding", {}) or {}).get("threat", {}) or {}
        for indicator in threat.get("indicators", []):
            family = str(indicator.get("family", "")).lower().replace(" ", "_")
            if family and family not in known_families and "unknown" not in family:
                return True
    except Exception:
        pass
    return False
