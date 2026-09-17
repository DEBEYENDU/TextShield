# Performance Report — V2.2

**Generated:** 2026-09-03 via `benchmarks/suite.py --iterations 20 --store --report`

## Summary
All 9 benchmarks within thresholds (see `benchmarks/report.json`). No regressions.

| Benchmark | Mean ms | p50 | p95 | Thr | Status |
|---|---|---|---|---|---|
| single_message | 42.1 (cold 2741) | 38.5 | 68.2 | 4000 | pass |
| batch 10 | 380.4 | 365 | 520 | 8000 | pass |
| ioc_extraction | 8.2 | 7.1 | 14.3 | 80 | pass |
| threat_lookup | 12.4 | 11.8 | 18.9 | 200 | pass |
| cache_latency | 0.85 | 0.78 | 1.42 | 10 | pass |
| rag_retrieval | 22.5 | 20.1 | 35.4 | 200 | pass |
| ml_inference | 9.8 | 9.2 | 13.5 | 100 | pass |
| api_latency | 18.3 | 16.9 | 28.7 | 150 | pass |
| dashboard_loading | 6.1 | 5.4 | 9.8 | 150 | pass |

*Cold single_message spike (2741ms) due to model load on first cold start; warm avg 42ms after cache.

## Improvements Since V2.1
- Cache hit_ratio 0.86 → 0.89 after LRU + WAL tuning; read latency 1.2ms → 0.85ms (30% faster).
- DB indexes: history pagination `EXPLAIN QUERY PLAN` now uses `idx_analyses_timestamp_id` (no SCAN).
- API latency 24ms → 18ms via `RateLimit` early-exit for health probes.
- RAG retrieval 30ms → 22ms via `SEMANTIC_CACHE_SIZE` 512.

## History
Stored in `benchmarks/history.json` (last 100 runs). Trend flat.

## Profiling
`python -m benchmarks.suite --only ioc_extraction --iterations 100` + `cProfile` shows regex dominates; pre-compiled patterns.

## Next
- Vectorize semantic batch; target 15ms RAG.
- Move SQLite → Postgres for concurrent writes.
