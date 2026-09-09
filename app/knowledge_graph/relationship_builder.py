"""Per-message context graph builder.

Turns understanding output (entities + profile + indicators) into a small
typed graph rooted at a MESSAGE node, e.g.::

    Technolearn --PART_OF--> Campus Drive --PART_OF--> Recruitment
    Google Forms --LINKS_TO--> Registration Link
    MESSAGE --MENTIONS--> ...
"""

from __future__ import annotations

import hashlib
import re

from app.knowledge_graph import GROUP_TO_TYPE
from app.knowledge_graph.edge import Edge
from app.knowledge_graph.entity_linker import EntityLinker
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.node import Node

_URL_LIKE = re.compile(r"https?://|www\.|bit\.ly|tinyurl|\.com|\.in\b", re.IGNORECASE)


class RelationshipBuilder:
    """Build a message-scoped context graph from understanding output."""

    def __init__(self, linker: EntityLinker | None = None):
        self.linker = linker or EntityLinker()

    def build(self, text: str, entities: dict, profile: dict,
              threat: dict | None = None, legitimacy: dict | None = None,
              sender: str = "") -> KnowledgeGraph:
        threat = threat or {}
        legitimacy = legitimacy or {}
        graph = KnowledgeGraph()
        message_id = "MESSAGE:" + hashlib.sha256(
            (text or "").encode("utf-8", errors="replace")).hexdigest()[:16]
        graph.add_node(Node(id=message_id, type="EVENT", label="Message",
                            normalized=message_id.lower(),
                            attrs={"category": profile.get("category", "Unknown"),
                                   "intent": profile.get("intent", "Inform")}))

        node_ids: dict[str, str] = {}  # (group, value) -> node id
        for group, items in (entities or {}).items():
            if group == "total_count" or group not in GROUP_TO_TYPE or not items:
                continue
            for item in items:
                value = item.get("value", "") if isinstance(item, dict) else str(item)
                conf = float(item.get("confidence", 0.7)) if isinstance(item, dict) else 0.7
                if not value:
                    continue
                etype, normalized, label = self.linker.link(group, value)
                nid = self.linker.node_id(etype, normalized)
                graph.add_node(Node(id=nid, type=etype, label=label,
                                    normalized=normalized, confidence=conf,
                                    attrs={"group": group}))
                node_ids[(group, value)] = nid
                graph.add_edge(Edge(src=message_id, dst=nid, rel="MENTIONS",
                                    weight=conf, evidence=value[:60]))

        self._semantic_edges(graph, node_ids, entities or {}, text or "")
        self._threat_edges(graph, message_id, node_ids, entities or {}, threat)
        self._sender_edges(graph, message_id, sender)
        return graph

    # ------------------------------------------- known-entity gazetteer pass
    def link_known(self, graph: KnowledgeGraph, text: str,
                   knowledge: "KnowledgeGraph") -> KnowledgeGraph:
        """Match message text against accumulated graph entities.

        Catches known organizations the regex extractor misses
        (e.g. bare "Technolearn"), answering "Is this organization known?"
        directly from graph memory.
        """
        lowered = f" {(text or '').lower()} "
        message_roots = [n for n in graph.nodes if n.startswith("MESSAGE:")]
        if not message_roots:
            return graph
        root = message_roots[0]
        for node in knowledge.nodes.values():
            if node.type not in {"ORGANIZATION", "BANK", "COMPANY", "UNIVERSITY",
                                 "COLLEGE", "GOVERNMENT", "CAMPAIGN", "SCAM"}:
                continue
            if node.id in graph.nodes:
                continue
            hit = False
            for candidate in {node.normalized, node.label.lower()}:
                if not candidate or len(candidate) < 3:
                    continue
                if re.search(r"(?<![a-z])" + re.escape(candidate) + r"(?![a-z])",
                             lowered):
                    hit = True
                    break
            if not hit:
                continue
            graph.add_node(Node(id=node.id, type=node.type, label=node.label,
                                normalized=node.normalized, confidence=0.6,
                                attrs={"group": "gazetteer"}))
            graph.add_edge(Edge(src=root, dst=node.id, rel="MENTIONS",
                                weight=0.6,
                                evidence=f"known entity mentioned: {node.label}"))
        return graph

    # ------------------------------------------------------- semantic edges
    def _semantic_edges(self, graph: KnowledgeGraph, node_ids: dict,
                        entities: dict, text: str) -> None:
        def first(group: str) -> str | None:
            items = entities.get(group, [])
            if not items:
                return None
            value = items[0].get("value", "") if isinstance(items[0], dict) else str(items[0])
            return node_ids.get((group, value))

        # recruiters / people work for companies / organizations
        for group in ("recruiters", "people"):
            for item in entities.get(group, []):
                value = item.get("value", "") if isinstance(item, dict) else str(item)
                src = node_ids.get((group, value))
                if not src:
                    continue
                for target_group in ("companies", "organizations", "banks", "universities"):
                    dst = first(target_group)
                    if dst and dst != src:
                        graph.add_edge(Edge(src=src, dst=dst, rel="WORKS_FOR",
                                            weight=0.7, evidence=value[:60]))
                        break
        # universities / colleges are part of education events
        uni = first("universities")
        if uni:
            for grp, items in entities.items():
                if grp in {"dates"} and items:
                    value = items[0].get("value", "") if isinstance(items[0], dict) else str(items[0])
                    dst = node_ids.get((grp, value))
                    if dst:
                        graph.add_edge(Edge(src=uni, dst=dst, rel="PART_OF",
                                            weight=0.6, evidence="campus event"))
        # urls hosted by / linking to domains
        for item in entities.get("urls", []):
            value = item.get("value", "") if isinstance(item, dict) else str(item)
            src = node_ids.get(("urls", value))
            host = self.linker.link("domains", value)[1]
            dst = graph.find_by_normalized(host, "DOMAIN")
            if src and dst and dst.id != src:
                graph.add_edge(Edge(src=src, dst=dst.id, rel="HOSTED_BY",
                                    weight=0.9, evidence=host[:60]))
        # emails registered to domains
        for item in entities.get("email_addresses", []):
            value = item.get("value", "") if isinstance(item, dict) else str(item)
            if "@" not in value:
                continue
            src = node_ids.get(("email_addresses", value))
            domain = value.rsplit("@", 1)[-1].lower()
            dst = graph.find_by_normalized(domain)
            if src and dst and dst.id != src:
                graph.add_edge(Edge(src=src, dst=dst.id, rel="REGISTERED_TO",
                                    weight=0.8, evidence=domain[:60]))
        # job roles belong to organizations
        for item in entities.get("job_titles", []):
            value = item.get("value", "") if isinstance(item, dict) else str(item)
            src = node_ids.get(("job_titles", value))
            dst = first("companies") or first("organizations") or first("banks")
            if src and dst:
                graph.add_edge(Edge(src=src, dst=dst, rel="BELONGS_TO",
                                    weight=0.6, evidence=value[:60]))

    # --------------------------------------------------------- threat edges
    def _threat_edges(self, graph: KnowledgeGraph, message_id: str, node_ids: dict,
                      entities: dict, threat: dict) -> None:
        families = {str(i.get("family", "")).lower()
                    for i in threat.get("indicators", [])}
        texts = " ".join(str(i.get("evidence", "")) for i in threat.get("indicators", []))
        if families & {"impersonation", "credential_harvesting", "sensitive_info_request"}:
            # mentioned orgs impersonate the trusted entity named nearby
            org_nodes = [node_ids[(g, self._val(entities, g))]
                         for g in ("banks", "companies", "organizations", "government_departments")
                         if self._val(entities, g)]
            for nid in org_nodes:
                if nid:
                    graph.add_edge(Edge(src=message_id, dst=nid, rel="IMPERSONATES",
                                        weight=0.8, evidence=texts[:80] or "impersonation"))
        if families & {"suspicious_url", "typosquatting", "homograph"}:
            for item in entities.get("urls", []):
                value = item.get("value", "") if isinstance(item, dict) else str(item)
                src = node_ids.get(("urls", value))
                if src:
                    graph.add_edge(Edge(src=src, dst=message_id, rel="ATTACKS",
                                        weight=0.7, evidence=value[:60]))
        if families & {"lottery", "investment_scam", "crypto_scam", "reward_bait"}:
            scam_id = "SCAM:" + sorted(families & {"lottery", "investment_scam",
                                                   "crypto_scam", "reward_bait"})[0]
            graph.add_node(Node(id=scam_id, type="SCAM",
                                label=scam_id.split(":", 1)[1].replace("_", " ").title(),
                                normalized=scam_id.split(":", 1)[1]))
            graph.add_edge(Edge(src=message_id, dst=scam_id, rel="TARGETS",
                                weight=0.8, evidence=texts[:80]))

    @staticmethod
    def _val(entities: dict, group: str) -> str:
        items = entities.get(group, [])
        if not items:
            return ""
        return items[0].get("value", "") if isinstance(items[0], dict) else str(items[0])

    # --------------------------------------------------------- sender edges
    def _sender_edges(self, graph: KnowledgeGraph, message_id: str, sender: str) -> None:
        if not sender or "@" not in sender:
            return
        etype, normalized, label = self.linker.link("email_addresses", sender)
        nid = self.linker.node_id(etype, normalized)
        graph.add_node(Node(id=nid, type=etype, label=label, normalized=normalized))
        graph.add_edge(Edge(src=nid, dst=message_id, rel="PUBLISHED_BY",
                            weight=0.9, evidence=sender[:60]))
