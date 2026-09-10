"""Structured decision explanations (RFC-007 example shape).

Final risk, per-source reasons in plain language, and calibrated
confidence — every claim traces to a recorded contribution.
"""

from __future__ import annotations


def build_explanation(decision: dict, analysis: dict) -> dict:
    """Render the adaptive decision as a human-readable explanation."""
    contributions = decision.get("contributions", []) or []
    reasons: list[str] = []
    for contrib in contributions[:6]:
        source = contrib["source"]
        p = contrib["p_spam"]
        ev = (contrib.get("evidence") or [""])[0][:90]
        if p >= 0.6:
            reasons.append(f"{_label(source)} flagged risk ({ev}).".strip())
        elif p <= 0.4:
            reasons.append(f"{_label(source)} found {_benign_phrase(source)} ({ev}).".strip())
    if not reasons:
        reasons.append("Evidence was mixed with no dominant signal.")
    profile = analysis.get("message_profile", {}) or {}
    agents = (analysis.get("agent_report", {}) or {}).get("agents", [])
    if agents:
        reasons.append(f"Specialist agents consulted: {', '.join(a.replace('Agent', '') for a in agents[:4])}.")
    return {
        "final_risk": decision.get("risk", "Low"),
        "decision": decision.get("decision", "HAM"),
        "reasons": reasons[:8],
        "confidence": f"{float(decision.get('confidence', 0.0)):.0%}",
        "confidence_raw": decision.get("confidence", 0.0),
        "policy": decision.get("policy", "balanced"),
        "category": decision.get("category", "Unknown"),
        "top_contributors": [
            {"source": c["source"], "share": c["share"], "p_spam": c["p_spam"]}
            for c in contributions[:4]],
        "uncertainty": decision.get("uncertainty", 0.0),
        "context": str(profile.get("overall_context", "")),
    }


def _label(source: str) -> str:
    return {"ml": "The ML classifier",
            "threat_intel": "Threat intelligence",
            "behavior": "Behavior analysis",
            "agents": "The multi-agent consensus",
            "graph": "The knowledge graph",
            "rag": "Retrieved knowledge",
            "legitimacy": "Legitimacy analysis",
            "llm": "LLM reasoning",
            "intent": "Intent analysis",
            "message_type": "Message-type analysis",
            "entities": "Entity analysis",
            "history": "Historical similarity"}.get(source, source.replace("_", " ").title())


def _benign_phrase(source: str) -> str:
    return {"legitimacy": "legitimacy markers",
            "graph": "a known organization",
            "behavior": "no urgency or coercion",
            "threat_intel": "no threat indicators",
            "agents": "a legitimate pattern",
            "rag": "benign precedents",
            "ml": "a benign pattern"}.get(source, "no concerns")
