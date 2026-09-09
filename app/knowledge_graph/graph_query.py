"""Graph query API: connected entities, paths, neighbors, similarity,
campaign / organization / domain / URL history."""

from __future__ import annotations

from app.knowledge_graph.entity_linker import EntityLinker
from app.knowledge_graph.graph import KnowledgeGraph

_linker = EntityLinker()


class GraphQuery:
    """Read-only queries over the accumulated knowledge graph."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    # ------------------------------------------------------- generic queries
    def connected_entities(self, node_id: str, rel: str | None = None,
                           max_results: int = 20) -> list[dict]:
        return [n.to_dict() for n in
                self.graph.neighbors(node_id, rel=rel)[:max_results]]

    def shortest_path(self, src: str, dst: str) -> list[str]:
        return self.graph.shortest_path(src, dst)

    def neighbor_search(self, node_id: str, type_name: str | None = None,
                        max_results: int = 20) -> list[dict]:
        out = []
        for node in self.graph.neighbors(node_id):
            if type_name is None or node.type == type_name:
                out.append(node.to_dict())
            if len(out) >= max_results:
                break
        return out

    def similarity(self, a: str, b: str) -> float:
        return self.graph.similarity(a, b)

    def similar_nodes(self, node_id: str, top_k: int = 5) -> list[dict]:
        scored = []
        for nid, node in self.graph.nodes.items():
            if nid == node_id or node.type == "EVENT":
                continue
            score = self.graph.similarity(node_id, nid)
            if score > 0:
                scored.append((score, node))
        scored.sort(key=lambda t: -t[0])
        return [{"score": s, **n.to_dict()} for s, n in scored[:top_k]]

    # ------------------------------------------------------- history lookups
    def _history(self, group: str, value: str) -> dict | None:
        etype, normalized, _ = _linker.link(group, value)
        node = self.graph.find_by_normalized(normalized, etype)
        if node is None and etype != "DOMAIN" and group in {"urls", "websites"}:
            node = self.graph.find_by_normalized(normalized, "DOMAIN")
        if node is None:
            return None
        return {
            "node": node.to_dict(),
            "sightings": node.sightings,
            "threat_hits": node.threat_hits,
            "legit_hits": node.legit_hits,
            "neighbors": [n.to_dict() for n in self.graph.neighbors(node.id)[:10]],
        }

    def campaign_lookup(self, name: str) -> dict | None:
        for etype in ("CAMPAIGN", "SCAM", "ATTACK_PATTERN"):
            node = self.graph.find_by_normalized(
                _linker.link("organizations", name)[1], etype)
            if node is not None:
                return self._history("organizations", node.label) or {
                    "node": node.to_dict(), "sightings": node.sightings,
                    "threat_hits": node.threat_hits, "legit_hits": node.legit_hits,
                    "neighbors": []}
        # fuzzy: substring over campaign/scam nodes
        needle = name.strip().lower()
        for node in self.graph.nodes.values():
            if node.type in {"CAMPAIGN", "SCAM", "ATTACK_PATTERN"} and needle in node.normalized:
                return {"node": node.to_dict(), "sightings": node.sightings,
                        "threat_hits": node.threat_hits, "legit_hits": node.legit_hits,
                        "neighbors": [n.to_dict() for n in self.graph.neighbors(node.id)[:10]]}
        return None

    def organization_history(self, name: str) -> dict | None:
        for group in ("banks", "companies", "organizations", "universities",
                      "government_departments"):
            hit = self._history(group, name)
            if hit is not None:
                return hit
        return None

    def domain_history(self, domain: str) -> dict | None:
        return self._history("domains", domain)

    def url_history(self, url: str) -> dict | None:
        hit = self._history("urls", url)
        if hit is not None:
            return hit
        return self._history("domains", url)
