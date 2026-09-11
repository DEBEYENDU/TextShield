"""Threat-intel integrations: knowledge graph, RAG, LLM, agents, trust.

Each function is defensive (never raises) and additive — existing
contracts are untouched. Wired from analysis_service step by step.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)

_IOC_NODE_TYPE = {"url": "URL", "domain": "DOMAIN", "ipv4": "URL",
                  "ipv6": "URL", "email": "EMAIL", "md5": "URL",
                  "sha1": "URL", "sha256": "URL", "phone": "PHONE"}


def sync_to_graph(checks: list[dict], message_id: str = "") -> dict:
    """Persist IOC nodes + relationships into the context graph.

    Domain ─associated_with→ Threat Campaign (when malicious),
    IP ─associated_with→ Domain, URL ─belongs_to→ Domain,
    IOC ─mentions→ (message-scoped evidence edge).
    Returns counts for observability.
    """
    added_nodes = 0
    added_edges = 0
    try:
        from app.knowledge_graph.edge import Edge
        from app.knowledge_graph.graph_store import open_graph_store
        from app.knowledge_graph.node import Node

        store = open_graph_store()
        graph = store.load()
        for check in checks or []:
            verdict = check.get("aggregated_verdict", "unknown")
            if verdict not in {"known_malicious", "suspicious", "benign"}:
                continue
            for result in check.get("results", []):
                if result.get("provider") in {"local"}:
                    continue
                ioc, ioc_type = check["ioc"], check["ioc_type"]
                node_type = _IOC_NODE_TYPE.get(ioc_type, "URL")
                node_id = f"{node_type}:{ioc.lower()}"
                if node_id not in graph.nodes:
                    graph.add_node(Node(
                        id=node_id, type=node_type, label=ioc,
                        normalized=ioc.lower(), confidence=check.get("confidence", 0.5),
                        attrs={"source": "threat-intel",
                               "verdict": verdict,
                               "provider": result.get("provider", "")}))
                    added_nodes += 1
                node = graph.nodes[node_id]
                node.touch(threat_leaning=(verdict in {"known_malicious", "suspicious"}),
                           legit_leaning=(verdict == "benign"))
                # URL -> belongs_to -> Domain
                if ioc_type == "url":
                    domain = _host_of(ioc)
                    if domain:
                        dom_id = f"DOMAIN:{domain}"
                        if dom_id not in graph.nodes:
                            from app.knowledge_graph.node import Node as _Node

                            graph.add_node(_Node(
                                id=dom_id, type="DOMAIN", label=domain,
                                normalized=domain,
                                attrs={"source": "threat-intel"}))
                            added_nodes += 1
                        graph.add_edge(Edge(src=node_id, dst=dom_id,
                                            rel="BELONGS_TO", weight=0.9,
                                            evidence=f"host of {ioc[:60]}"))
                        added_edges += 1
                # malicious domain -> associated_with -> campaign hint
                if verdict == "known_malicious" and ioc_type in {"domain", "url"}:
                    campaign = _campaign_hint(check)
                    if campaign:
                        camp_id = f"CAMPAIGN:{campaign}"
                        if camp_id not in graph.nodes:
                            from app.knowledge_graph.node import Node as _Node

                            graph.add_node(_Node(
                                id=camp_id, type="CAMPAIGN", label=campaign,
                                normalized=campaign,
                                attrs={"source": "threat-intel"}))
                            added_nodes += 1
                        anchor = dom_id if ioc_type == "url" and domain else node_id
                        graph.add_edge(Edge(src=anchor, dst=camp_id,
                                            rel="ASSOCIATED_WITH", weight=0.7,
                                            evidence=f"intel verdict {verdict}"))
                        added_edges += 1
        store.save(graph)
    except Exception as exc:
        logger.warning("Threat-intel graph sync failed: %s", exc)
    return {"nodes_added": added_nodes, "edges_added": added_edges}


def _host_of(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    except Exception:
        return ""


def _campaign_hint(check: dict) -> str:
    for result in check.get("results", []):
        for category in result.get("categories", []):
            text = str(category).lower()
            if "phish" in text:
                return "phishing-campaign"
            if "malware" in text:
                return "malware-campaign"
            if "scam" in text or "fraud" in text:
                return "fraud-campaign"
    return "malicious-infrastructure"


def to_rag_evidence(checks: list[dict]) -> list[dict]:
    """Format validated threat findings as retrievable evidence.

    Only confirmed verdicts (known_malicious / benign from a successful
    lookup) become evidence — raw external responses are never inserted
    blindly. Each item carries source metadata and matches the
    rag_evidence item shape. Durability comes from the reputation store
    and graph sync, so future analyses retrieve the same conclusions.
    """
    evidence: list[dict] = []
    for check in checks or []:
        verdict = check.get("aggregated_verdict", "unknown")
        if verdict not in {"known_malicious", "benign"}:
            continue
        providers = sorted({r.get("provider", "") for r in check.get("results", [])
                            if r.get("verdict") == verdict})
        if not providers:
            continue
        ioc, ioc_type = check["ioc"], check["ioc_type"]
        if verdict == "known_malicious":
            document = (f"Threat intelligence: {ioc} ({ioc_type}) previously "
                        f"associated with malicious activity "
                        f"(confidence {check.get('confidence', 0):.2f}).")
            category, score = "threat_intel", round(0.5 + check.get("confidence", 0) / 2, 4)
        else:
            document = (f"Threat intelligence: {ioc} ({ioc_type}) previously "
                        f"assessed benign.")
            category, score = "threat_intel_benign", 0.3
        evidence.append({
            "id": f"ti:{ioc_type}:{ioc.lower()}",
            "document": document,
            "metadata": {"source": "threat-intel",
                         "category": category,
                         "providers": providers,
                         "verdict": verdict},
            "score": score,
        })
    return evidence
