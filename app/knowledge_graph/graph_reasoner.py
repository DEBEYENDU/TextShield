"""Graph reasoner: answer contextual questions, adjust trust & threat.

Questions answered per message:
- Is this organization known?            -> known_organizations (+trust)
- Has this domain appeared before?       -> known/unknown domains (-trust if new + risky)
- Is this URL tied to previous campaigns?-> campaign_matches (+threat)
- Does this resemble earlier legitimate communications? (+trust)
- Are entities connected to known scams? (+threat)

Output ``trust_adjustment`` / ``threat_adjustment`` are deltas in [-0.3, +0.3]
applied by callers to *adjusted_* fields only — never to stored scores.
"""

from __future__ import annotations

from app.knowledge_graph.entity_linker import EntityLinker
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.graph_query import GraphQuery

TRUSTED_ATTRS = {"trusted"}
MALICIOUS_ATTRS = {"malicious"}


class GraphReasoner:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.query = GraphQuery(graph)
        self.linker = EntityLinker()

    def reason(self, message_graph: KnowledgeGraph, profile: dict,
               threat: dict, legitimacy: dict) -> dict:
        reasons: list[str] = []
        known_orgs: list[str] = []
        unknown_domains: list[str] = []
        known_domains: list[str] = []
        campaign_matches: list[str] = []
        scam_links: list[str] = []
        trust_delta = 0.0
        threat_delta = 0.0

        msg_nodes = [n for nid, n in message_graph.nodes.items()
                     if not nid.startswith("MESSAGE:")]

        for node in msg_nodes:
            known = self.graph.nodes.get(node.id)
            # --- organizations / banks / universities / government
            if node.type in {"ORGANIZATION", "BANK", "COMPANY", "UNIVERSITY",
                             "COLLEGE", "GOVERNMENT"}:
                if known is not None and known.attrs.get("trusted"):
                    known_orgs.append(node.label)
                    trust_delta += 0.08
                    reasons.append(f"Organization known & trusted: {node.label} "
                                   f"({known.sightings} prior sightings)")
                elif known is not None:
                    known_orgs.append(node.label)
                    trust_delta += 0.03
                    reasons.append(f"Organization seen before: {node.label}")
                # scam proximity: path to any malicious node?
                scam = self._nearest_malicious(node.id)
                if scam is not None:
                    path = self.graph.shortest_path(node.id, scam)
                    if path:
                        scam_links.append(node.label)
                        threat_delta += 0.10
                        reasons.append(f"{node.label} is {len(path) - 1} hop(s) from "
                                       f"known malicious entity {self.graph.nodes[scam].label}")
            # --- domains / urls / emails
            if node.type in {"DOMAIN", "URL", "WEBSITE", "EMAIL"}:
                host = node.normalized.rsplit("@", 1)[-1] if "@" in node.normalized else node.normalized
                hist = (self.query.domain_history(host)
                        or self.query.url_history(node.normalized))
                if hist is not None:
                    known_domains.append(host)
                    if hist["threat_hits"] > hist["legit_hits"]:
                        threat_delta += 0.10
                        reasons.append(f"Domain {host} appeared in "
                                       f"{hist['threat_hits']} prior threat message(s)")
                    else:
                        trust_delta += 0.03
                        reasons.append(f"Domain {host} seen before without threat history")
                else:
                    if host not in unknown_domains:
                        unknown_domains.append(host)
            # --- campaigns / scams mentioned
            if node.type in {"CAMPAIGN", "SCAM", "ATTACK_PATTERN"}:
                hit = self.query.campaign_lookup(node.normalized.replace("_", " "))
                if hit is not None:
                    campaign_matches.append(hit["node"]["label"])
                    threat_delta += 0.12
                    reasons.append(f"Known campaign pattern: {hit['node']['label']}")

        # URL nodes in the message graph that match known campaigns by neighbor
        for node in msg_nodes:
            if node.type == "URL":
                for nid, other in self.graph.nodes.items():
                    if other.type in {"CAMPAIGN", "SCAM"} and \
                            self.graph.similarity(node.id, nid) > 0:
                        pass  # similarity across stores is per-graph; skip

        # resemblance to earlier legitimate communications
        legit_nodes = [n for n in self.graph.nodes.values()
                       if n.legit_hits > n.threat_hits and n.type != "EVENT"]
        similar_legit = 0
        for node in msg_nodes:
            if node.type in {"ORGANIZATION", "BANK", "COMPANY", "UNIVERSITY",
                             "GOVERNMENT", "DOMAIN"}:
                known = self.graph.nodes.get(node.id)
                if known is not None and known.legit_hits > known.threat_hits:
                    similar_legit += known.legit_hits
        if similar_legit:
            trust_delta += min(0.10, 0.02 * similar_legit)
            reasons.append(f"Entities resemble {similar_legit} earlier legitimate "
                           f"communication(s)")

        if unknown_domains and (threat.get("threat_score", 0) or 0) >= 0.3:
            threat_delta += 0.05
            reasons.append(f"Unknown domain(s) in a threat-leaning message: "
                           f"{', '.join(unknown_domains[:3])}")

        trust_delta = round(max(-0.3, min(0.3, trust_delta)), 3)
        threat_delta = round(max(-0.3, min(0.3, threat_delta)), 3)

        base_trust = float(profile.get("trust_score", 0.5) or 0.5)
        base_threat = float(profile.get("threat_score", 0.5) or 0.0)
        confidence = "High" if (known_orgs or campaign_matches) else (
            "Medium" if (known_domains or reasons) else "Low")

        return {
            "known_organizations": sorted(set(known_orgs)),
            "known_domains": sorted(set(known_domains)),
            "unknown_domains": sorted(set(unknown_domains)),
            "campaign_matches": sorted(set(campaign_matches)),
            "scam_linked_entities": sorted(set(scam_links)),
            "similar_message_count": similar_legit,
            "threat_history": ("Known malicious pattern: " + ", ".join(sorted(set(campaign_matches)))
                               if campaign_matches else None),
            "trust_adjustment": trust_delta,
            "threat_adjustment": threat_delta,
            "adjusted_trust": round(max(0.0, min(1.0, base_trust + trust_delta)), 3),
            "adjusted_threat": round(max(0.0, min(1.0, base_threat + threat_delta)), 3),
            "confidence": confidence,
            "reasons": reasons,
            "headline_relationships": self._headline_relationships(message_graph),
        }

    # ---------------------------------------------------------------- helpers
    def _nearest_malicious(self, node_id: str) -> str | None:
        node = self.graph.nodes.get(node_id)
        if node is None:
            return None
        for neighbor in self.graph.neighbors(node_id):
            if neighbor.attrs.get("malicious"):
                return neighbor.id
        for neighbor in self.graph.neighbors(node_id):
            for second in self.graph.neighbors(neighbor.id):
                if second.attrs.get("malicious"):
                    return second.id
        return None

    @staticmethod
    def _headline_relationships(message_graph: KnowledgeGraph) -> list[str]:
        out = []
        for edge in message_graph.edges.values():
            if edge.src.startswith("MESSAGE:") or edge.dst.startswith("MESSAGE:"):
                continue
            src = message_graph.nodes.get(edge.src)
            dst = message_graph.nodes.get(edge.dst)
            if src and dst:
                out.append(f"{src.label} --{edge.rel}--> {dst.label}")
            if len(out) >= 5:
                break
        return out
