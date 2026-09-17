"""Structured multi-agent report generation (RFC-005 example shape)."""

from __future__ import annotations


def build_report(ctx_dict: dict, agent_reports: list[dict], consensus: dict,
                 fused: dict, latency_ms: float) -> dict:
    """Assemble the unified evidence report."""
    agents_run = [r["name"] for r in agent_reports]
    summary = _summarize(ctx_dict, agent_reports, consensus, fused)
    return {
        "overall_risk": consensus.get("overall_risk", "Low"),
        "consensus": consensus.get("consensus", "Uncertain"),
        "message_type": ctx_dict.get("category", "Unknown"),
        "intent": ctx_dict.get("intent", "Inform"),
        "agents": agents_run,
        "agent_reports": agent_reports,
        "evidence": fused,
        "confidence": consensus.get("confidence", 0.0),
        "trust_score": consensus.get("trust_score", 0.0),
        "threat_score": consensus.get("risk_score", 0.0),
        "entities": ctx_dict.get("entities", {}),
        "knowledge": {
            "retrieved_documents": fused.get("retrieved_knowledge", 0),
            "supporting_documents": fused.get("supporting_documents", []),
            "graph_reasons": fused.get("graph_evidence", []),
            "behavior_triggers": fused.get("behavior_evidence", []),
        },
        "conflicts": consensus.get("conflicts", []),
        "summary": summary["text"],
        "recommendation": summary["recommendation"],
        "latency_ms": round(latency_ms, 2),
    }


def _summarize(ctx_dict: dict, agent_reports: list[dict], consensus: dict,
               fused: dict) -> dict:
    category = ctx_dict.get("category", "Unknown")
    top_agents = sorted(agent_reports,
                        key=lambda r: r.get("relevance", 0.0),
                        reverse=True)[:4]
    agent_names = ", ".join(r["name"].replace("Agent", "") for r in top_agents)
    neg = len(fused.get("negative_evidence", []))
    pos = len(fused.get("positive_evidence", []))
    if consensus.get("overall_risk") in {"High", "Medium"} and neg:
        headline = f"Likely {category.lower()} with {neg} risk signal(s)."
    elif pos:
        headline = f"Likely {category.lower()} notice."
    else:
        headline = f"{category} message with mixed signals."
    details = []
    if neg:
        details.append(fused["negative_evidence"][0].split("] ", 1)[-1][:80])
    if pos:
        details.append(fused["positive_evidence"][0].split("] ", 1)[-1][:80])
    text = f"{headline} Agents [{agent_names}]. " + " ".join(details)
    risky = [r for r in agent_reports if r.get("risk_score", 0.0) >= 0.5
             and r.get("relevance", 0.0) >= 0.3]
    if risky:
        recommendation = risky[0].get("recommended_action", "Verify independently.")
    else:
        calm = [r for r in top_agents if r.get("trust_score", 0.0) >= 0.6]
        recommendation = (calm[0].get("recommended_action",
                                      "Proceed normally.") if calm
                          else "Proceed normally but verify links independently.")
    return {"text": text[:600], "recommendation": recommendation}
