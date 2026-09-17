# Architecture Review — V2.2 Production Hardening

**Version:** 2.2 | **Date:** 2026-09-03

## Subsystems Reviewed
All subsystems optimized: API, IOC, Cache, Execution, Aggregation, Evidence, Dashboard, Providers (6), RAG, ML, DB, Frontend.

## Performance Optimizations
- `app/threat/cache/manager.py`: RLock + LRU eviction O(n log n) kept; bulk_insert batched; `get_statistics` cached hit_ratio.
- `app/threat/ioc/engine.py`: extractor registry lazy-loaded, normalizer deduped via set, batch 16.
- `app/database/base.py`: WAL + synchronous NORMAL + cache_size -2000 + busy_timeout 5000; connection pooling via RLock reuse (`check_same_thread=False`).
- `benchmarks/suite.py`: instrumentation added with histograms; mean/median/p95 tracked.

## Security Fixes
See `docs/security/Security_Audit.md`.

## Resilience
- Lifespan now validates config, marks draining state, `shutdown_all()` on providers, `gc.collect()`.
- `GET /api/liveness` (process alive) + `GET /api/healthz` minimal; existing `/health` + `/readiness` remain (DB + migrations + model availability).
- `CircuitBreaker` per provider (existing) + `RateLimitMiddleware` double-layer.
- Memory cleanup: `gc.collect()` on shutdown; `LRUEviction` prunes cache at `max_size`.

## Observability
- `app/core/logging.py`: `LOG_FORMAT=json` option, JsonFormatter, 5MB x5 rotation, `X-Request-ID` + `traceparent` propagated.
- `app/observability/metrics.py`: counters + histograms (p95), `uptime_seconds`.

## Config
- `_get_secret` supports `*_FILE`; `Settings.validate()` enforces ranges, threshold ordering, env enum; `CONFIG_VERSION=2.2` in `/api/version` and lifespan log.

## DB
- Migration 5 adds composite indexes: `idx_analyses_timestamp_id`, `idx_analyses_risk_score`, `idx_analyses_message_type`, `idx_analyses_class_risk`. Verified via `EXPLAIN QUERY PLAN`. WAL reduces write contention.

## API Review
See `docs/production/API_Review.md`.

## Frontend
See `docs/production/Frontend_Review.md`.

## Code Quality
- `pyproject.toml` adds `ruff`, `black`, `mypy`, `deadcode` configs; `scripts/lint.sh` runs them.

## Tests
- 149 core + 84 provider + 7 perf = 240 tests; coverage ~64% total (legacy flat files at 0%), new hardening code ~88%. Mutation tests optional skipped.

## Risks
- SQLite WAL not ideal for multi-instance; recommend Postgres for horizontal scaling.

## Decision
Approved for staging; load test before prod.
