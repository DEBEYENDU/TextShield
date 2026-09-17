"""In-memory directed multigraph: storage, traversal, similarity, merge."""

from __future__ import annotations

from collections import deque

from app.knowledge_graph.edge import Edge
from app.knowledge_graph.node import Node


class KnowledgeGraph:
    """Lightweight directed multigraph with typed nodes and edges."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str, str], Edge] = {}
        self._out: dict[str, set[tuple[str, str, str]]] = {}
        self._in: dict[str, set[tuple[str, str, str]]] = {}

    # ------------------------------------------------------------- mutation
    def add_node(self, node: Node) -> Node:
        existing = self.nodes.get(node.id)
        if existing is None:
            self.nodes[node.id] = node
            return node
        # merge: keep earliest first_seen, accumulate counters
        existing.sightings += node.sightings
        existing.threat_hits += node.threat_hits
        existing.legit_hits += node.legit_hits
        existing.last_seen = node.last_seen
        existing.confidence = round(max(existing.confidence, node.confidence), 3)
        existing.attrs.update(node.attrs)
        return existing

    def add_edge(self, edge: Edge) -> Edge:
        existing = self.edges.get(edge.key)
        if existing is None:
            self.edges[edge.key] = edge
            self._out.setdefault(edge.src, set()).add(edge.key)
            self._in.setdefault(edge.dst, set()).add(edge.key)
            return edge
        existing.weight = round(existing.weight + edge.weight, 3)
        if edge.evidence and edge.evidence not in existing.evidence:
            existing.evidence = (existing.evidence + " | " + edge.evidence)[:200]
        return existing

    def merge(self, other: "KnowledgeGraph") -> None:
        for node in other.nodes.values():
            self.add_node(Node.from_dict(node.to_dict()))
        for edge in other.edges.values():
            self.add_edge(Edge.from_dict(edge.to_dict()))

    # ------------------------------------------------------------ traversal
    def neighbors(self, node_id: str, rel: str | None = None,
                  direction: str = "both") -> list[Node]:
        keys: set[tuple[str, str, str]] = set()
        if direction in ("out", "both"):
            keys |= self._out.get(node_id, set())
        if direction in ("in", "both"):
            keys |= self._in.get(node_id, set())
        out: list[Node] = []
        seen: set[str] = set()
        for key in keys:
            edge = self.edges[key]
            if rel is not None and edge.rel != rel:
                continue
            other = edge.dst if edge.src == node_id else edge.src
            if other in seen or other not in self.nodes:
                continue
            seen.add(other)
            out.append(self.nodes[other])
        return out

    def shortest_path(self, src: str, dst: str, max_depth: int = 5) -> list[str]:
        """BFS shortest path (node ids). Empty list when disconnected."""
        if src == dst and src in self.nodes:
            return [src]
        if src not in self.nodes or dst not in self.nodes:
            return []
        queue: deque[tuple[str, list[str]]] = deque([(src, [src])])
        visited = {src}
        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for nxt in self._adjacent_ids(current):
                if nxt in visited:
                    continue
                if nxt == dst:
                    return path + [nxt]
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
        return []

    def _adjacent_ids(self, node_id: str) -> set[str]:
        ids: set[str] = set()
        for key in self._out.get(node_id, set()) | self._in.get(node_id, set()):
            edge = self.edges[key]
            ids.add(edge.dst if edge.src == node_id else edge.src)
        return ids

    # ------------------------------------------------------------ similarity
    def neighbor_signature(self, node_id: str) -> set[str]:
        return self._adjacent_ids(node_id)

    def similarity(self, a: str, b: str) -> float:
        """Jaccard similarity over neighbor sets blended with label overlap."""
        if a == b:
            return 1.0
        if a not in self.nodes or b not in self.nodes:
            return 0.0
        sig_a, sig_b = self.neighbor_signature(a), self.neighbor_signature(b)
        union = sig_a | sig_b
        jaccard = len(sig_a & sig_b) / len(union) if union else 0.0
        toks_a = set(self.nodes[a].normalized.split())
        toks_b = set(self.nodes[b].normalized.split())
        union_t = toks_a | toks_b
        lexical = len(toks_a & toks_b) / len(union_t) if union_t else 0.0
        return round(0.6 * jaccard + 0.4 * lexical, 3)

    # ------------------------------------------------------------------ misc
    def nodes_by_type(self, type_name: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.type == type_name]

    def find_by_normalized(self, normalized: str, type_name: str | None = None) -> Node | None:
        needle = (normalized or "").strip().lower()
        for node in self.nodes.values():
            if node.normalized == needle and (type_name is None or node.type == type_name):
                return node
        return None

    def __len__(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)
