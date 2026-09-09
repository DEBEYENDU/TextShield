"""Frontend-ready serializers: Cytoscape, D3.js, Graphviz, plain dict."""

from __future__ import annotations

from app.knowledge_graph.graph import KnowledgeGraph

_TYPE_COLORS = {
    "PERSON": "#4C9AFF", "ORGANIZATION": "#6554C0", "BANK": "#006644",
    "COLLEGE": "#974F0C", "UNIVERSITY": "#974F0C", "COMPANY": "#6554C0",
    "GOVERNMENT": "#403294", "WEBSITE": "#00B8D9", "DOMAIN": "#00B8D9",
    "URL": "#00B8D9", "EMAIL": "#C1C7D0", "PHONE": "#C1C7D0",
    "SOCIAL_MEDIA": "#FFAB00", "EVENT": "#FF5630", "JOB_ROLE": "#4C9AFF",
    "TECHNOLOGY": "#00B8D9", "MALWARE": "#DE350B", "CAMPAIGN": "#DE350B",
    "ATTACK_PATTERN": "#FF7452", "SCAM": "#DE350B", "PAYMENT_PLATFORM": "#006644",
}


def to_dict(graph: KnowledgeGraph) -> dict:
    return {
        "nodes": [n.to_dict() for n in graph.nodes.values()],
        "edges": [e.to_dict() for e in graph.edges.values()],
        "node_count": len(graph.nodes),
        "edge_count": graph.edge_count(),
    }


def to_cytoscape(graph: KnowledgeGraph) -> dict:
    """``{elements: {nodes: [{data}], edges: [{data}]}}`` for Cytoscape.js."""
    return {
        "elements": {
            "nodes": [
                {"data": {"id": n.id, "label": n.label, "type": n.type,
                           "color": _TYPE_COLORS.get(n.type, "#8993A4"),
                           "sightings": n.sightings,
                           "threat_hits": n.threat_hits, "legit_hits": n.legit_hits}}
                for n in graph.nodes.values()
            ],
            "edges": [
                {"data": {"id": f"{e.src}::{e.rel}::{e.dst}", "source": e.src,
                           "target": e.dst, "label": e.rel, "weight": e.weight}}
                for e in graph.edges.values()
            ],
        }
    }


def to_d3(graph: KnowledgeGraph) -> dict:
    """``{nodes: [...], links: [...]}`` for D3.js force layouts."""
    ids = list(graph.nodes.keys())
    index = {nid: i for i, nid in enumerate(ids)}
    return {
        "nodes": [{"id": nid, "label": graph.nodes[nid].label,
                   "type": graph.nodes[nid].type,
                   "color": _TYPE_COLORS.get(graph.nodes[nid].type, "#8993A4")}
                  for nid in ids],
        "links": [{"source": index[e.src], "target": index[e.dst],
                   "rel": e.rel, "value": e.weight}
                  for e in graph.edges.values()
                  if e.src in index and e.dst in index],
    }


def to_dot(graph: KnowledgeGraph, name: str = "context_graph") -> str:
    """Graphviz DOT source."""
    lines = [f'digraph "{name}" {{', '  rankdir=LR;']
    for node in graph.nodes.values():
        label = node.label.replace('"', "'")[:40]
        lines.append(f'  "{node.id}" [label="{label}\\n({node.type})"];')
    for edge in graph.edges.values():
        lines.append(f'  "{edge.src}" -> "{edge.dst}" [label="{edge.rel}"];')
    lines.append("}")
    return "\n".join(lines)


def llm_context_block(summary: dict) -> str:
    """Render reasoner output as the LLM prompt section (RFC-003 example)."""
    lines = ["GRAPH CONTEXT (entity & relationship evidence):"]
    orgs = summary.get("known_organizations", [])
    lines.append(f"Known Organization: {', '.join(orgs) if orgs else '(none)'}")
    rels = summary.get("headline_relationships", [])
    lines.append(f"Relationship: {'; '.join(rels) if rels else '(none)'}")
    lines.append(f"Previous Similar Messages: {summary.get('similar_message_count', 0)}")
    lines.append(f"Threat History: {summary.get('threat_history') or 'None'}")
    lines.append(f"Confidence: {summary.get('confidence', 'Low')}")
    notes = summary.get("reasons", [])
    if notes:
        lines.append("Graph Notes:")
        lines.extend(f"- {note}" for note in notes[:8])
    return "\n".join(lines)
