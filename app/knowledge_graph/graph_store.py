"""Graph storage with provider abstraction.

Providers: ``memory`` (ephemeral), ``json`` (persistent file, default),
``neo4j`` (future — raises a clear error until the driver is configured).
Do NOT hardcode Neo4j: all access goes through ``GraphStore``.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.logging import get_logger
from app.knowledge_graph.edge import Edge
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.node import Node

logger = get_logger(__name__)

DEFAULT_GRAPH_PATH = Path("data/knowledge_graph.json")

# Seed knowledge: long-lived trusted entities + known scam campaigns.
# (surface form, entity type, attrs)
SEED_NODES: list[tuple[str, str, dict]] = [
    ("State Bank of India", "BANK", {"trusted": True, "sector": "banking"}),
    ("HDFC Bank", "BANK", {"trusted": True, "sector": "banking"}),
    ("ICICI Bank", "BANK", {"trusted": True, "sector": "banking"}),
    ("Punjab National Bank", "BANK", {"trusted": True, "sector": "banking"}),
    ("Reserve Bank of India", "GOVERNMENT", {"trusted": True, "sector": "regulator"}),
    ("Income Tax Department", "GOVERNMENT", {"trusted": True, "sector": "tax"}),
    ("UIDAI", "GOVERNMENT", {"trusted": True, "sector": "identity"}),
    ("Technolearn", "ORGANIZATION", {"trusted": True, "sector": "education"}),
    ("Delhi University", "UNIVERSITY", {"trusted": True, "sector": "education"}),
    ("KYC Scam", "CAMPAIGN", {"malicious": True, "pattern": "credential harvesting"}),
    ("Courier Customs Scam", "CAMPAIGN", {"malicious": True, "pattern": "fee fraud"}),
    ("Investment Doubling Scam", "CAMPAIGN", {"malicious": True, "pattern": "fake returns"}),
    ("UPI Collect Scam", "CAMPAIGN", {"malicious": True, "pattern": "collect request"}),
    ("Remote Access Refund Scam", "CAMPAIGN", {"malicious": True, "pattern": "anydesk"}),
    ("Credential Theft", "ATTACK_PATTERN", {"malicious": True}),
    ("Lottery Fraud", "SCAM", {"malicious": True}),
    ("Romance Fraud", "SCAM", {"malicious": True}),
]

SEED_EDGES: list[tuple[str, str, str]] = [
    ("BANK:state bank of india", "GOVERNMENT:reserve bank of india", "REPORTS"),
    ("CAMPAIGN:kyc scam", "BANK:state bank of india", "IMPERSONATES"),
    ("CAMPAIGN:kyc scam", "ATTACK_PATTERN:credential theft", "USES"),
    ("CAMPAIGN:courier customs scam", "SCAM:lottery fraud", "ASSOCIATED_WITH"),
    ("CAMPAIGN:upi collect scam", "ATTACK_PATTERN:credential theft", "USES"),
    ("CAMPAIGN:remote access refund scam", "ATTACK_PATTERN:credential theft", "USES"),
]


class GraphStore(ABC):
    """Storage backend contract (Neo4j-compatible interface)."""

    backend_name = "base"

    @abstractmethod
    def load(self) -> KnowledgeGraph: ...

    @abstractmethod
    def save(self, graph: KnowledgeGraph) -> None: ...

    @abstractmethod
    def merge_message_graph(self, message_graph: KnowledgeGraph,
                            *, threat_leaning: bool = False,
                            legit_leaning: bool = False) -> None: ...


class MemoryGraphStore(GraphStore):
    backend_name = "memory"

    def __init__(self) -> None:
        self._graph = KnowledgeGraph()
        _seed(self._graph)

    def load(self) -> KnowledgeGraph:
        return self._graph

    def save(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def merge_message_graph(self, message_graph: KnowledgeGraph, *,
                            threat_leaning: bool = False,
                            legit_leaning: bool = False) -> None:
        _merge_with_touch(self._graph, message_graph, threat_leaning, legit_leaning)


class JsonFileGraphStore(GraphStore):
    backend_name = "json"

    def __init__(self, path: str | Path = DEFAULT_GRAPH_PATH) -> None:
        self.path = Path(path)
        self._graph: KnowledgeGraph | None = None

    def load(self) -> KnowledgeGraph:
        if self._graph is not None:
            return self._graph
        graph = KnowledgeGraph()
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                for raw in data.get("nodes", []):
                    graph.add_node(Node.from_dict(raw))
                for raw in data.get("edges", []):
                    graph.add_edge(Edge.from_dict(raw))
                logger.info("Knowledge graph loaded: %d nodes from %s",
                            len(graph.nodes), self.path)
            except Exception as exc:
                logger.warning("Graph load failed (%s); reseeding", exc)
                graph = KnowledgeGraph()
        if not graph.nodes:
            _seed(graph)
        self._graph = graph
        return graph

    def save(self, graph: KnowledgeGraph) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": "1.0",
                       "nodes": [n.to_dict() for n in graph.nodes.values()],
                       "edges": [e.to_dict() for e in graph.edges.values()]}
            self.path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
            self._graph = graph
        except Exception as exc:
            logger.warning("Graph save failed: %s", exc)

    def merge_message_graph(self, message_graph: KnowledgeGraph, *,
                            threat_leaning: bool = False,
                            legit_leaning: bool = False) -> None:
        graph = self.load()
        _merge_with_touch(graph, message_graph, threat_leaning, legit_leaning)
        self.save(graph)


class Neo4jGraphStore(GraphStore):
    """Future Neo4j backend — same interface, driver wired when configured."""

    backend_name = "neo4j"

    def __init__(self, uri: str = "", user: str = "", password: str = "") -> None:
        self.uri, self.user, self.password = uri, user, password

    def _driver(self):
        try:
            import neo4j  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "Neo4j backend requested but the `neo4j` driver is not installed. "
                "Install it and set GRAPH_STORE=neo4j with NEO4J_URI/USER/PASSWORD."
            ) from exc
        return neo4j.GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def load(self) -> KnowledgeGraph:
        raise NotImplementedError(
            "Neo4j LOAD cypher mapping is a future extension; "
            "use the `json` backend for now.")

    def save(self, graph: KnowledgeGraph) -> None:
        raise NotImplementedError(
            "Neo4j SAVE cypher mapping is a future extension; "
            "use the `json` backend for now.")

    def merge_message_graph(self, message_graph: KnowledgeGraph, *,
                            threat_leaning: bool = False,
                            legit_leaning: bool = False) -> None:
        raise NotImplementedError(
            "Neo4j MERGE cypher mapping is a future extension; "
            "use the `json` backend for now.")


def _seed(graph: KnowledgeGraph) -> None:
    from app.knowledge_graph.entity_linker import EntityLinker

    linker = EntityLinker()
    for surface, etype, attrs in SEED_NODES:
        normalized = linker.link(
            {"BANK": "banks", "GOVERNMENT": "government_departments",
             "UNIVERSITY": "universities"}.get(etype, "organizations"), surface)[1]
        graph.add_node(Node(id=f"{etype}:{normalized}", type=etype,
                            label=surface, normalized=normalized,
                            confidence=0.95, sightings=0, attrs=attrs))
    for src, dst, rel in SEED_EDGES:
        if src in graph.nodes and dst in graph.nodes:
            graph.add_edge(Edge(src=src, dst=dst, rel=rel, weight=1.0,
                                evidence="seed knowledge"))


def _merge_with_touch(graph: KnowledgeGraph, message_graph: KnowledgeGraph,
                      threat_leaning: bool, legit_leaning: bool) -> None:
    for node in message_graph.nodes.values():
        if node.type == "EVENT":  # message roots stay per-message, not global
            continue
        existing = graph.nodes.get(node.id)
        if existing is None:
            fresh = Node.from_dict(node.to_dict())
            fresh.sightings = 1
            fresh.threat_hits = 1 if threat_leaning else 0
            fresh.legit_hits = 1 if legit_leaning else 0
            graph.add_node(fresh)
        else:
            existing.touch(threat_leaning=threat_leaning,
                           legit_leaning=legit_leaning,
                           confidence=node.confidence)
    for edge in message_graph.edges.values():
        if edge.src.startswith("MESSAGE:") or edge.dst.startswith("MESSAGE:"):
            continue
        graph.add_edge(Edge.from_dict(edge.to_dict()))


_store: GraphStore | None = None


def open_graph_store(backend: str | None = None, path: str | Path | None = None) -> GraphStore:
    """Factory: ``memory`` | ``json`` (default) | ``neo4j`` (future)."""
    import os

    global _store
    name = (backend or os.getenv("GRAPH_STORE", "json")).lower()
    if name == "memory":
        return MemoryGraphStore()
    if name == "neo4j":
        return Neo4jGraphStore(uri=os.getenv("NEO4J_URI", ""),
                               user=os.getenv("NEO4J_USER", ""),
                               password=os.getenv("NEO4J_PASSWORD", ""))
    if _store is None or getattr(_store, "path", None) != (Path(path) if path else DEFAULT_GRAPH_PATH):
        _store = JsonFileGraphStore(path or DEFAULT_GRAPH_PATH)
    return _store
