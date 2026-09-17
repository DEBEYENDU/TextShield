# RFC-003 Implementation Report — Entity & Context Knowledge Graph (v4.0)

**Branch:** `v2.2-dev` | **Status:** All acceptance criteria satisfied

## Architecture

New package `app/knowledge_graph/` (10 modules): `node`/`edge`/`graph`
(model + BFS + similarity), `entity_linker` (aliases: SBI≡State Bank of
India; domain/phone/email normalization), `relationship_builder`
(per-message graph + gazetteer pass), `graph_store` (memory/json/neo4j-stub
providers, seeded knowledge, per-message learning), `graph_query` (7 query
kinds), `graph_reasoner` (5 questions → bounded trust/threat deltas +
`build_and_reason` orchestration), `serializers` (dict/Cytoscape/D3/DOT/LLM
block). Integration is additive with try/except guards: `analysis_service`
gains `knowledge_graph` + `graph_rag_evidence` result keys; `generator`
gains a GRAPH CONTEXT prompt section; primary RAG/risk/classification paths
are byte-identical.

## Entity model & graph examples

- Technolearn campus drive → `Technolearn—MENTIONS—MESSAGE`,
  `known_organizations=[Technolearn]`, trust +0.08, confidence High.
- Fake SBI KYC (`bit.ly` + OTP) → `known_organizations=[State Bank of
  India]`, `campaign_matches=[KYC Scam]`, threat +0.15–0.27, expansion
  terms `[State Bank of India, KYC Scam, phishing URL]`, verdict
  `Threat History: Known malicious pattern: KYC Scam`.

## Integration points

| Consumer | Mechanism |
|---|---|
| RAG | expansion terms → second retrieval → `graph_rag_evidence` (deduped, ≤3, primary list untouched) |
| Trust engine | `trust_adjustment`/`adjusted_trust` (known org +0.08, legit resemblance up to +0.10) |
| Threat | `threat_adjustment`/`adjusted_threat` (campaign +0.12, scam proximity +0.10, unknown domain +0.05) |
| LLM | GRAPH CONTEXT block (Known Organization / Relationship / Previous Similar / Threat History / Confidence) |
| Frontend | Cytoscape elements embedded per analysis (`visualization`) |

## Benchmarks

- 25/25 new tests pass (linking, traversal, persistence round-trip,
  reasoning, serializers, integration).
- Full suite: **500 passed** (475 pre-existing + 25), 0 regressions.
- Reasoner overhead: regex/BFS only, single-digit ms (no model loads).

## Future extensions

- Neo4j Cypher LOAD/SAVE/MERGE behind the existing `GraphStore` interface.
- Cross-message entity coreference (campaign tracking over time).
- Embedding-backed `similar_nodes` for fuzzy org matching.
- Feeding `adjusted_*` scores into `compute_risk` behind a feature flag.
- Frontend graph view consuming the embedded Cytoscape payload.
