# TextShield v4.0 — Entity & Context Knowledge Graph (RFC-003)

Reason with context instead of isolated words. The graph sits beside the
understanding pipeline (RFC-001) and trust/threat scoring (RFC-002) and
feeds RAG retrieval and LLM prompts. It never classifies.

## Architecture

```text
understanding entities ─▶ EntityLinker ─▶ RelationshipBuilder ─▶ message graph
                                                        │
persistent store (json) ◀── merge/learn ── build_and_reason ──▶ verdict
        │                                                        ├── trust/threat adjustments
        ├── RAG expansion terms ──▶ extra retrieval ──▶ graph_rag_evidence
        └── LLM GRAPH CONTEXT block ──▶ generator prompt
```

## Entity model

21 types (`PERSON` … `PAYMENT_PLATFORM`, see `app/knowledge_graph/__init__.py`).
Node: `{id: "TYPE:normalized", type, label, normalized, confidence,
first_seen, last_seen, sightings, threat_hits, legit_hits, attrs}`.
Seed knowledge ships trusted entities (SBI/HDFC/ICICI/PNB, RBI, UIDAI,
Technolearn, Delhi University) and malicious patterns (KYC/Courier/UPI/
refund campaigns, credential theft, lottery/romance scams).

## Relationship model

17 relations (`WORKS_FOR` … `PUBLISHED_BY`). Per-message edges derive from
semantics (recruiter→company, email→domain, URL→host, role→org), threat
families (`IMPERSONATES`, `ATTACKS`, `TARGETS`→SCAM nodes), sender
(`PUBLISHED_BY`), plus a gazetteer pass resolving known entities the regex
extractor misses. Traversal is undirected (context discovery); BFS shortest
path; Jaccard+lexical similarity.

## Query API (`GraphQuery`)

`connected_entities`, `shortest_path`, `neighbor_search`,
`similarity`/`similar_nodes`, `campaign_lookup`, `organization_history`,
`domain_history`, `url_history`.

## Serialization

`to_dict` (persist), `to_cytoscape` (Cytoscape.js elements), `to_d3`
(nodes/links), `to_dot` (Graphviz), `llm_context_block` (prompt section).

## Storage providers

`GRAPH_STORE=memory|json|neo4j` via `open_graph_store()`. Default `json`
persists to `data/knowledge_graph.json` and learns sightings/threat/legit
counters per message. `neo4j` exposes the same interface and raises a clear
setup error until the driver is configured (future Cypher mapping).

## Reasoner verdict

Answers: org known? domain seen? URL↔campaign? resembles legit history?
scam proximity? Emits `trust_adjustment`/`threat_adjustment` (±0.3 bounded)
as `adjusted_*` fields only — stored scores are never rewritten.
