"""RFC-003 tests: knowledge graph model, linking, traversal, reasoning,
persistence, serializers and RAG/trust/LLM integration."""

from __future__ import annotations

import pytest

from app.knowledge_graph import GROUP_TO_TYPE, RELATIONSHIPS
from app.knowledge_graph.edge import Edge
from app.knowledge_graph.entity_linker import EntityLinker, normalize_domain, normalize_phone
from app.knowledge_graph.graph import KnowledgeGraph
from app.knowledge_graph.graph_query import GraphQuery
from app.knowledge_graph.graph_reasoner import GraphReasoner, build_and_reason
from app.knowledge_graph.graph_store import (
    JsonFileGraphStore,
    MemoryGraphStore,
    Neo4jGraphStore,
    open_graph_store,
)
from app.knowledge_graph.node import Node
from app.knowledge_graph.relationship_builder import RelationshipBuilder
from app.knowledge_graph.serializers import (
    llm_context_block,
    to_cytoscape,
    to_d3,
    to_dict,
    to_dot,
)
from app.understanding.entities import entity_extractor
from app.understanding.pipeline import understanding_pipeline

CAMPUS = ("Dear Students, Technolearn placement cell announces a campus drive. "
          "Register via the Google Form link. No fees.")
FAKE_SBI = ("URGENT: State Bank of India KYC suspended! Verify your login at "
            "http://bit.ly/sbi-kyc-verify now and share your OTP to avoid closure.")


def _understanding(text: str) -> dict:
    return understanding_pipeline.analyze(text)


def _memory() -> MemoryGraphStore:
    return MemoryGraphStore()


# ------------------------------------------------------------ model & linker
def test_entity_types_covered():
    for group in ("people", "banks", "domains", "urls", "universities",
                  "job_titles", "money"):
        assert group in GROUP_TO_TYPE


def test_linker_merges_sbi_aliases():
    linker = EntityLinker()
    ids = {linker.link("banks", v)[:2] for v in
           ("SBI", "State Bank", "State Bank of India")}
    assert len(ids) == 1
    assert ids.pop()[1] == "state bank of india"


def test_linker_normalizes_domains_phones():
    assert normalize_domain("WWW.Bit.Ly ") == "bit.ly"
    assert normalize_domain("https://example.com/path") == "example.com"
    assert normalize_phone("+91 98200 12345") == "9820012345"


def test_graph_add_merge_and_counts():
    g = KnowledgeGraph()
    g.add_node(Node(id="BANK:sbi", type="BANK", label="SBI", normalized="sbi"))
    g.add_node(Node(id="BANK:sbi", type="BANK", label="SBI",
                    normalized="sbi", sightings=2))
    assert g.nodes["BANK:sbi"].sightings == 3
    g.add_edge(Edge(src="A", dst="B", rel="MENTIONS"))
    g.add_edge(Edge(src="A", dst="B", rel="MENTIONS"))
    assert g.edge_count() == 1
    assert g.edges[("A", "B", "MENTIONS")].weight == 2.0


# ------------------------------------------------------------ builder
def test_relationship_builder_message_graph():
    u = _understanding(CAMPUS)
    g = RelationshipBuilder().build(CAMPUS, u["entities"], u["profile"],
                                    u["threat"], u["legitimacy"])
    assert any(nid.startswith("MESSAGE:") for nid in g.nodes)
    assert g.edge_count() >= 1
    assert all(e.rel in RELATIONSHIPS for e in g.edges.values())


def test_builder_threat_edges_for_phish():
    u = _understanding(FAKE_SBI)
    g = RelationshipBuilder().build(FAKE_SBI, u["entities"], u["profile"],
                                    u["threat"], u["legitimacy"])
    rels = {e.rel for e in g.edges.values()}
    assert rels & {"IMPERSONATES", "ATTACKS", "TARGETS", "MENTIONS"}


def test_gazetteer_links_known_org():
    store = _memory()
    u = _understanding(CAMPUS)
    builder = RelationshipBuilder()
    g = builder.build(CAMPUS, u["entities"], u["profile"], u["threat"], u["legitimacy"])
    builder.link_known(g, CAMPUS, store.load())
    assert "ORGANIZATION:technolearn" in g.nodes


# ------------------------------------------------------------ traversal
def _chain() -> KnowledgeGraph:
    g = KnowledgeGraph()
    for nid in ("A", "B", "C", "D"):
        g.add_node(Node(id=nid, type="ORGANIZATION", label=nid, normalized=nid.lower()))
    g.add_edge(Edge(src="A", dst="B", rel="PART_OF"))
    g.add_edge(Edge(src="B", dst="C", rel="PART_OF"))
    g.add_edge(Edge(src="A", dst="D", rel="MENTIONS"))
    return g


def test_neighbors_and_shortest_path():
    g = _chain()
    assert {n.id for n in g.neighbors("A")} == {"B", "D"}
    assert g.shortest_path("A", "C") == ["A", "B", "C"]
    # traversal is undirected (context discovery): C reaches D via B, A
    assert g.shortest_path("C", "D") == ["C", "B", "A", "D"]
    assert g.shortest_path("A", "ZZZ") == []


def test_similarity_reflexive_and_zero():
    g = _chain()
    assert g.similarity("A", "A") == 1.0
    assert g.similarity("A", "ZZZ") == 0.0
    assert 0.0 <= g.similarity("B", "D") <= 1.0


# ------------------------------------------------------------ store
def test_memory_store_seeded_and_merges(tmp_path=None):
    store = _memory()
    g = store.load()
    assert store.backend_name == "memory"
    assert g.find_by_normalized("state bank of india", "BANK") is not None
    assert g.find_by_normalized("kyc scam", "CAMPAIGN") is not None


def test_json_store_persistence_roundtrip(tmp_path):
    path = tmp_path / "graph.json"
    store = JsonFileGraphStore(path)
    g = store.load()
    assert len(g.nodes) >= 10  # seeds
    u = _understanding(CAMPUS)
    mg = RelationshipBuilder().build(CAMPUS, u["entities"], u["profile"],
                                     u["threat"], u["legitimacy"])
    store.merge_message_graph(mg, legit_leaning=True)
    reloaded = JsonFileGraphStore(path).load()
    assert len(reloaded.nodes) >= len(g.nodes)
    assert path.exists()


def test_store_factory_and_neo4j_stub():
    assert open_graph_store(backend="memory").backend_name == "memory"
    assert open_graph_store(backend="json",
                            path="/tmp/ts_graph_factory_probe.json").backend_name == "json"
    neo = Neo4jGraphStore()
    with pytest.raises((NotImplementedError, RuntimeError)):
        neo.load()


# ------------------------------------------------------------ query
def test_query_histories_and_campaign():
    q = GraphQuery(_memory().load())
    org = q.organization_history("SBI")
    assert org is not None and org["node"]["type"] == "BANK"
    camp = q.campaign_lookup("KYC Scam")
    assert camp is not None and camp["node"]["type"] == "CAMPAIGN"
    assert q.domain_history("no-such-domain-xyz.test") is None
    assert q.url_history("http://no-such-domain-xyz.test/a") is None


def test_query_connected_and_similar():
    g = _chain()
    q = GraphQuery(g)
    assert len(q.connected_entities("A")) == 2
    assert q.shortest_path("A", "C") == ["A", "B", "C"]
    assert isinstance(q.similar_nodes("A"), list)


# ------------------------------------------------------------ reasoner
def test_reasoner_known_org_raises_trust():
    store = _memory()
    out = build_and_reason(CAMPUS, _understanding(CAMPUS), store=store)
    v = out["verdict"]
    assert "Technolearn" in v["known_organizations"]
    assert v["trust_adjustment"] > 0
    assert v["adjusted_trust"] >= 0.5


def test_reasoner_fake_sbi_matches_campaign():
    store = _memory()
    out = build_and_reason(FAKE_SBI, _understanding(FAKE_SBI), store=store)
    v = out["verdict"]
    assert "KYC Scam" in v["campaign_matches"]
    assert v["threat_adjustment"] > 0
    assert "State Bank of India" in out["expansion_terms"]
    assert "KYC Scam" in out["expansion_terms"]


def test_reasoner_unknown_domain_noted():
    store = _memory()
    out = build_and_reason(FAKE_SBI, _understanding(FAKE_SBI), store=store)
    assert any("bit.ly" in d for d in out["verdict"]["unknown_domains"])


def test_reasoner_adjustments_bounded():
    store = _memory()
    v = build_and_reason(FAKE_SBI, _understanding(FAKE_SBI), store=store)["verdict"]
    assert -0.3 <= v["trust_adjustment"] <= 0.3
    assert -0.3 <= v["threat_adjustment"] <= 0.3
    assert 0.0 <= v["adjusted_trust"] <= 1.0
    assert 0.0 <= v["adjusted_threat"] <= 1.0


def test_reasoner_learns_across_messages(tmp_path):
    store = JsonFileGraphStore(tmp_path / "learn.json")
    build_and_reason(CAMPUS, _understanding(CAMPUS), store=store)
    q = GraphQuery(store.load())
    tech = q.organization_history("Technolearn")
    assert tech is not None and tech["sightings"] >= 1


# ------------------------------------------------------------ serializers
def test_serializers_shapes():
    g = _chain()
    d = to_dict(g)
    assert d["node_count"] == 4 and d["edge_count"] == 3
    cy = to_cytoscape(g)
    assert "elements" in cy and len(cy["elements"]["nodes"]) == 4
    d3 = to_d3(g)
    assert len(d3["nodes"]) == 4 and len(d3["links"]) == 3
    dot = to_dot(g)
    assert "digraph" in dot and "PART_OF" in dot


def test_llm_context_block_matches_rfc_example():
    block = llm_context_block({
        "known_organizations": ["Technolearn"],
        "headline_relationships": ["Technolearn --PART_OF--> Campus Recruitment"],
        "similar_message_count": 18,
        "threat_history": None,
        "confidence": "High",
        "reasons": [],
    })
    for line in ("Known Organization:", "Technolearn", "Campus Recruitment",
                 "Previous Similar Messages: 18", "Threat History: None",
                 "Confidence: High"):
        assert line in block


# ------------------------------------------------------------ integration
def test_entity_extraction_feeds_graph():
    ents = entity_extractor.extract("State Bank of India alert: contact sbi.co.in")
    assert ents["total_count"] >= 1
    u = _understanding("State Bank of India alert: contact sbi.co.in")
    g = RelationshipBuilder().build("x", u["entities"], u["profile"],
                                    u["threat"], u["legitimacy"])
    assert len(g.nodes) >= 2


def test_analysis_includes_knowledge_graph():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(AnalyzeRequest(message=CAMPUS),
                                      store_history=False)
    kg = result["knowledge_graph"]
    assert kg["node_count"] >= 1
    assert "Technolearn" in kg["known_organizations"]
    assert kg["trust_adjustment"] >= 0
    assert "graph_context" in kg and "Known Organization:" in kg["graph_context"]
    assert kg["visualization"]["elements"]
    # legacy contract untouched
    assert result["classification"] in {"SPAM", "HAM"}
    assert "risk_level" in result


def test_analysis_phish_graph_threat():
    from app.schemas.analysis import AnalyzeRequest
    from app.services import analysis_service

    result = analysis_service.analyze(AnalyzeRequest(message=FAKE_SBI),
                                      store_history=False)
    kg = result["knowledge_graph"]
    assert "KYC Scam" in kg["campaign_matches"]
    assert kg["threat_adjustment"] > 0
    assert isinstance(result["graph_rag_evidence"], list)


def test_generator_prompt_contains_graph_context():
    from app.rag.generator import _user_prompt

    prompt = _user_prompt({"message": "hi", "graph_context": "GRAPH CONTEXT (entity"})
    assert "GRAPH CONTEXT" in prompt
