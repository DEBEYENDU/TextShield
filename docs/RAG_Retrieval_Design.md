# RAG Retrieval Design Documentation

## Architecture

The RAG Retrieval Pipeline is a modular, deterministic, and configurable system that
retrieves, ranks, validates, and assembles cybersecurity knowledge evidence for
later reasoning by an LLM. The pipeline is designed to be LLM-agnostic - it
produces structured evidence output that can be consumed by any reasoning engine.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      INPUT: Semantic Features                        │
│  (topics, entities, intent, behavioral patterns, communication goal) │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: Query Builder                             │
│  Convert semantic features into 5 optimized search queries:          │
│  - Primary (broad semantic search)                                   │
│  - Intent (intent-based retrieval)                                   │
│  - Behavior (behavioral pattern retrieval)                           │
│  - Entity (entity-based retrieval)                                   │
│  - Context (context-based retrieval)                                 │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2-3: Multi-Query Retrieval                 │
│  Retrieve results independently for each query type using:           │
│  - Dense vector search over the knowledge store                      │
│  - Results grouped by query type (primary, intent, behavior, entity,  │
│    context)                                                        │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 4: Hybrid Retrieval                        │
│  Combine dense vector search with metadata filtering:                │
│  - Category filtering                                                │
│  - Tag filtering                                                     │
│  - Language filtering                                                │
│  - Trust level filtering                                             │
│  - Intelligent merge/deduplication of vector + metadata results      │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 5: Similarity Search                       │
│  Retrieve Top-K candidates with configurable:                      │
│  - Top-K                                                             │
│  - Minimum similarity threshold (0.35 default)                      │
│  - Maximum retrieval depth                                           │
│  - Maximum context size                                              │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 6: Re-Ranking                              │
│  Rank retrieved chunks using composite relevance score:               │
│  - Semantic similarity (base score from vector search)               │
│  - Intent relevance                                                    │
│  - Behavior relevance                                                  │
│  - Metadata quality                                                    │
│  - Trust level                                                         │
│  - Freshness (recency of last_updated)                               │
│  - Category relevance                                                  │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 7: Duplicate Removal                       │
│  Remove duplicate and near-duplicate chunks:                       │
│  - Content hash-based detection                                      │
│  - Source + category-based deduplication                             │
│  - Quality score filtering                                           │
│  - Keeps only highest-quality version of each unique chunk           │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 8: Evidence Validation                     │
│  Reject evidence if any condition fails:                            │
│  - Similarity below threshold (0.35 default)                        │
│  - Invalid metadata (missing required fields)                        │
│  - Untrusted knowledge source                                        │
│  - Incomplete chunks (missing document text)                         │
│  - Obsolete document version                                         │
│  Returns: valid_chunks, rejected_chunks, overall_confidence          │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 9: Context Construction                    │
│  Build final context for future LLM with:                         │
│  - Relevant knowledge (from validated chunks)                       │
│  - Behavioral explanations                                            │
│  - Manipulation techniques                                            │
│  - Examples (clearly legitimate/spam/phishing)                      │
│  - Counter-examples (legitimate patterns)                           │
│  - References (source, version, trust level)                        │
│  - Metadata (categories, trust levels, sources)                     │
│  - Does NOT include unnecessary information                         │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 10: Context Compression                    │
│  If retrieved evidence exceeds token limits:                       │
│  - Summarize knowledge chunks                                        │
│  - Deduplicate content across chunks                                 │
│  - Prioritize highest-relevance chunks                               │
│  - Maintain references and metadata                                  │
│  - Preserve essential explanations                                   │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 11: Retrieval Confidence                   │
│  Estimate confidence based on:                                      │
│  - Similarity (vector search scores)                                │
│  - Agreement between query types                                     │
│  - Metadata quality                                                   │
│  - Trust level                                                        │
│  - Coverage (how well detected topics are represented)               │
│  Returns: overall_confidence + factor breakdown                       │
└───────────────────────┬─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 12: Output Schema                          │
│  Structured return object:                                          │
│  {                                                                  │
│    "queries": [],         - The 5 query types used for retrieval    │
│    "retrieved_documents": [], - All chunks before dedup/reranking    │
│    "ranked_chunks": [],   - Reranked by composite relevance score      │
│    "supporting_examples": [], - Clearly legitimate/phishing examples  │
│    "counter_examples": [], - Legitimate communication patterns        │
│    "references": [],      - Source/version/trust citations            │
│    "retrieval_confidence": 0.93, - Overall confidence (0.0-1.0)     │
│    "coverage_score": 0.91, - Topic/entity coverage (0.0-1.0)        │
│    "context": "..." - Compressed context for future LLM              │
│  }                                                                 │
└───────────────────────────────────────────────────────────────────────┘

## Service Integration

The pipeline integrates with existing TextShield components:

### Semantic Engine
- Provides: topic names, entities, intent, behavioral patterns
- Input: pre-processed message text
- Output: SemanticFeatures dict consumed by QueryBuilder
- Integration point: `build_queries_from_semantic()`

### Intent Engine
- Provides: detected sender intent with confidence
- Integration: intent field in SemanticFeatures drives Intent query type
- No direct LLM classification - evidence only

### Knowledge Loader
- Provides: structured knowledge base documents from Phase 7
- Integration: vector store search, metadata-aware filtering
- Uses: `knowledge_loader.py` loaded documents

### Vector Store
- Backends: ChromaDB (primary) or SimpleVectorStore (fallback)
- Stores: document embeddings + metadata
- Integration: `open_vector_store()` + `store.query()` 
- No LLM connection - pure retrieval

### What is NOT connected:
- ✘ LLM prompts
- ✘ Final spam/ham classification
- ✘ Decision Engine
- ✘ Risk Engine
- ✘ Recommendation Engine

## Configuration

All parameters are configurable via the `RagConfig` class, overridable from
environment variables through the central `Settings` class.

### Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RAG_TOP_K` | 5 | Number of chunks to retrieve per query type |
| `RAG_MAX_CONTEXT_CHUNKS` | 5 | Max chunks in final context |
| `RAG_MAX_TOKEN_LIMIT` | 2000 | Max estimated tokens in context |
| `RAG_SIMILARITY_THRESHOLD` | 0.35 | Minimum similarity to accept chunk |
| `RERANK_INTENT_WEIGHT` | 0.20 | Weight for intent relevance in reranking |
| `RERANK_BEHAVIOR_WEIGHT` | 0.15 | Weight for behavior relevance |
| `RERANK_METADATA_WEIGHT` | 0.15 | Weight for metadata quality |
| `RERANK_TRUST_WEIGHT` | 0.10 | Weight for trust level |
| `RERANK_CATEGORY_WEIGHT` | 0.10 | Weight for category relevance |
| `RERANK_SIMILARITY_WEIGHT` | 0.30 | Weight for base semantic similarity |
| `RAG_INCLUDE_BEHAVIORAL` | True | Include behavioral explanations in context |
| `RAG_INCLUDE_EXAMPLES` | True | Include examples in context |
| `RAG_INCLUDE_COUNTER_EXAMPLES` | True | Include counter-examples in context |
| `RAG_ENABLE_CATEGORY_FILTER` | True | Enable category-based metadata filtering |
| `RAG_ENABLE_TAG_FILTER` | True | Enable tag-based metadata filtering |
| `RAG_ENABLE_LANGUAGE_FILTER` | True | Enable language code filtering |
| `RAG_ENABLE_TRUST_FILTER` | True | Enable trust level filtering |

### Environment Variables

All RagConfig parameters can be overridden via `.env` file entries:
```
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.35
RERANK_INTENT_WEIGHT=0.20
...
```

## Retrieval Flow

```text
Input Message
      │
      ▼
1. Semantic Feature Extraction
      │
      ▼
2. Query Builder → 5 Query Types
      │
      ▼
3. Multi-Query Retrieval (per type)
      │
      ▼
3b. Hybrid Retrieval (vector + metadata)
      │
      ▼
4. Result Merge & Deduplication
      │
      ▼
5. Re-Ranking (composite relevance score)
      │
      ▼
6. Evidence Validation (reject invalid)
      │
      ▼
7. Context Construction (structured)
      │
      ▼
8. Retrieval Confidence Estimation
      │
      ▼
9. Output Schema (structured object)
      │
      ▼
Output: RetrievalOutput JSON
```

## Evidence Validation Rules

Evidence is rejected if any of the following conditions are met:

1. **Similarity below threshold**: Vector search score < 0.35 (configurable)
2. **Invalid metadata**: Missing required fields (source, category, version, last_updated)
3. **Untrusted source**: trust_level not in (high, medium, low) or source not verifiable
4. **Incomplete chunk**: Missing document text, < 20 chars, or no source
5. **Obsolete version**: Version number < 1.0 considered potentially obsolete

Each valid chunk contributes to the overall retrieval confidence score:
- Similarity: 30% weight
- Agreement between query types: 25% weight
- Metadata quality: 20% weight
- Trust level: 15% weight
- Coverage of detected topics: 10% weight

## Limitations

1. **No LLM integration**: Pipeline returns evidence only; no final classification
2. **Embedding quality dependent**: Retrieval quality depends on embedding model used
3. **Metadata quality dependent**: Validation is only as good as document metadata
4. **Semantic features input quality**: Query builder output depends on semantic engine accuracy
5. **No world knowledge**: Retrieval limited to knowledge base documents (Phase 7)
6. **No real-time updating**: Vector store built at knowledge base build time
7. **Short text sparsity**: SMS/text messages with very little content may yield sparse results

## Performance Optimization

### Batch Retrieval
- Multiple messages can be embedded in parallel
- Vector store queries can be batched for same-query types
- Query builder can pre-compute common query combinations

### Parallel Search
- Five query types retrieved in parallel (Python async or thread pool)
- Hybrid filtering applies after parallel collection
- Reranking is the only sequential step (low latency)

### Caching
- Query embedding cache (TTL-based, cleared on knowledge rebuild)
- Result cache by (query_hash, config_hash) pair
- Similarity threshold cache for frequent queries

### Low Latency Targets
- Single message retrieval: < 2 seconds (CPU, sentence-transformers)
- Multi-message batch: < 5 seconds for 10 messages
- Cache hit ratio target: > 80% for repeated queries

### Incremental Updates
- New knowledge documents can be added to vector store without rebuild
- Query builder config changes take effect immediately
- Similarity threshold changes require cache clearing