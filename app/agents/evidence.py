"""Evidence fusion: merge agent opinions with pipeline evidence into
positive / negative / uncertain buckets plus supporting material."""

from __future__ import annotations


def fuse_evidence(agent_reports: list[dict], ctx_dict: dict,
                  rag_evidence: list | None = None) -> dict:
    """Combine agent findings with RAG, graph and behavior evidence."""
    positive: list[str] = []
    negative: list[str] = []
    uncertain: list[str] = []
    for report in agent_reports:
        weight = report.get("relevance", 0.0) * report.get("confidence", 0.0)
        for finding in report.get("findings", []):
            entry = f"[{report['name']}] {finding}"
            if report.get("risk_score", 0.0) >= 0.5 and weight >= 0.15:
                negative.append(entry)
            elif report.get("trust_score", 0.0) >= 0.6 and weight >= 0.15:
                positive.append(entry)
            else:
                uncertain.append(entry)
    supporting_docs = [
        f"{e.get('source', 'knowledge')} (score {e.get('score', 0.0)})"
        for e in (rag_evidence or [])[:5]
    ]
    case_studies = [
        e.get("source", "") for e in (rag_evidence or [])
        if "case" in str(e.get("source", "")).lower()
           or "study" in str(e.get("category", "")).lower()
    ][:3]
    graph_evidence = ctx_dict.get("graph_reasons", []) or []
    behavior_evidence = ctx_dict.get("behavior_triggers", []) or []
    agent_opinions = [
        {"agent": r["name"], "risk": r.get("risk_score", 0.0),
         "trust": r.get("trust_score", 0.0),
         "confidence": r.get("confidence", 0.0),
         "relevance": r.get("relevance", 0.0)}
        for r in agent_reports
    ]
    return {
        "positive_evidence": positive[:12],
        "negative_evidence": negative[:12],
        "uncertain_evidence": uncertain[:12],
        "supporting_documents": supporting_docs,
        "relevant_case_studies": case_studies,
        "retrieved_knowledge": len(rag_evidence or []),
        "graph_evidence": graph_evidence[:8],
        "behavior_evidence": behavior_evidence[:8],
        "agent_opinions": agent_opinions,
    }
