from __future__ import annotations

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from .models import EvidenceItem, EvidenceSource


class EvidenceGraph:
    """Internal evidence graph connecting all subsystems.

    Preserves full traceability: every node links back to its source,
    timestamp, and original evidence item. The frontend can display
    which subsystem produced each piece, when, why, and supporting artifacts.

    Graph structure (adjacency list):
        node_id -> { "type": str, "data": EvidenceItem, "links": [node_id, ...] }
    """

    def __init__(self):
        self._nodes: Dict[str, dict] = {}  # node_id -> info
        self._adj: Dict[str, List[str]] = {}  # node_id -> neighbour node_ids

    def add_node(self, node_id: str, evidence: EvidenceItem, node_type: str) -> None:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node.
            evidence: The EvidenceItem produced at this point.
            node_type: Human-readable type (e.g. "semantic_meaning", "ml_prediction").
        """
        self._nodes[node_id] = {
            "type": node_type,
            "data": evidence,
            "timestamp": evidence.timestamp,
            "source": evidence.source,
        }
        self._adj.setdefault(node_id, [])

    def add_link(self, from_id: str, to_id: str) -> None:
        """Add a directed link from one graph node to another.

        Args:
            from_id: Source node identifier.
            to_id: Target node identifier.
        """
        self._adj.setdefault(from_id, []).append(to_id)
        self._adj.setdefault(to_id, [])  # ensure target exists

    def get_node(self, node_id: str) -> Optional[dict]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[str]:
        return self._adj.get(node_id, [])

    def all_nodes(self) -> Dict[str, dict]:
        return self._nodes

    def paths_to(self, target_type: str) -> List[List[str]]:
        """Find all paths from any node to a node of target_type.

        Simple BFS for traceability queries.
        """
        # Collect start nodes (all nodes)
        start_nodes = list(self._nodes.keys())
        paths: List[List[str]] = []

        # BFS from each start
        for start in start_nodes:
            queue = [(start, [start])]
            visited = {start}
            while queue:
                (node, path) = queue.pop(0)
                node_data = self._nodes.get(node)
                if not node_data:
                    continue
                if node_data["type"] == target_type:
                    paths.append(path)
                    continue
                for neighbor in self._adj.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        return paths

    def trace_from(self, node_id: str) -> List[dict]:
        """Return the chain of nodes leading back to sources.

        Useful for the frontend to show provenance.
        """
        chain: List[dict] = []
        current = node_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            node_data = self._nodes.get(current)
            if not node_data:
                break
            chain.append({
                "node_id": current,
                "type": node_data["type"],
                "source": node_data["source"].value,
                "timestamp": node_data["timestamp"],
                "evidence_id": node_data["data"].evidence_id,
            })
            # move to predecessors – simple approach: look for nodes linking here
            # we reverse the adjacency: find nodes that have current as neighbor
            prevs = [n for n, neigh in self._adj.items() if current in neigh]
            if not prevs:
                break
            current = prevs[0]  # pick first predecessor
        return chain