# Changelog

All notable changes to **TextShield** follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-09-03

Stable v2.2.0 release — Threat Intelligence Platform + Production Hardening.

### Added
- **Threat Intelligence Core** (RFC-002): `app/threat/` registry, `ThreatIndicator`, `ProviderRegistry`, `IThreatProvider` abstraction, error types.
- **IOC Extraction Engine** (RFC-003): extractors for URL/Domain/IP/Email/Phone/Short-URL/QR/Crypto, normalizer, validator, registry, `IOCEngine`; `GET /api/v2/threat/ioc`.
- **Threat Cache** (RFC-004): `CacheRecord`, `InMemoryStorage`, `CacheManager` (CRUD, TTL, LRU/TTL eviction, revisions), `CacheStatistics`, `cleanup`, `serializer`; `GET/DELETE /api/v2/threat/cache`.
- **Async Lookup Engine** (RFC-005): `ThreatCoordinator`, `Executor` (semaphore 10), `RetryPolicy` exponential backoff+jitter, `TimeoutManager`, `CircuitBreaker`, `ConcurrencyLimiter`, `Scheduler`.
- **Initial Providers** (RFC-006): `GoogleSafeBrowsingProvider` + `VirusTotalProvider` (submodules `config/mapper/models/provider`), capabilities `url/malware/phishing/ip/hash`, cache/retry/rate-limit, health checks.
- **Reputation Aggregation** (RFC-007): `ReputationAggregator` with weighting, fusion, conflict resolution, confidence scoring, `ThreatProfile`.
- **Unified Evidence Integration** (RFC-008): `EvidenceEngine`, merger, confidence graph, `POST /api/v2/evidence`.
- **Threat Dashboard** (RFC-009): `app/analytics/{dashboards,metrics,history,summaries}`, `GET /dashboard/*` + `/api/v2/dashboard/*`, Chart.js frontend.
- **Extended Providers** (RFC-010): `OpenPhish` (feed), `PhishTank` (verified/valid), `URLhaus` (malware payloads), `AbuseIPDB` (IPv4/IPv6 abuse confidence) — each with `provider/client/mapper/models/validator/config`, `GET /api/v2/threat/providers/{openphish|phishtank|urlhaus|abuseipdb}`.
- **Benchmark Suite** (RFC-011): `benchmarks/suite.py` (9 targets: single/batch/IOC/threat/cache/RAG/ML/API/dashboard), `history.json` (100 runs), `report.json` with thresholds, `tests/test_performance.py`.
- **Observability:** `app/observability/metrics.py` counters/histograms, JSON log option (`LOG_FORMAT=json`), `X-Request-ID`+`traceparent` propagation.
- **Examples:** `examples/` (Python/JS/cURL/batch/webhook/plugin) + `docs/guides/*`.
- **CI:** `.github/workflows/ci.yml` (black, ruff, mypy, pytest --cov, benchmark, pip-audit, docs validation).

### Changed
- Version bump `1.0.0` → `2.2.0` across `app/__init__.py`, `pyproject.toml [project]`, `frontend/package.json`, `settings.CONFIG_VERSION`.
- `app/core/settings.py`: `_get_secret` supports `*_FILE` Docker secrets, `validate()` + `CONFIG_VERSION`, `_get` wraps secrets.
- `app/database/base.py`: PRAGMAs `WAL`, `NORMAL`, `cache_size -2000`, `busy_timeout 5000`, `check_same_thread=False`.
- `app/database/migrations.py`: migration 5 hardening indexes (`idx_analyses_timestamp_id`, `risk_score`, `message_type`, `class_risk`).
- `app/api/middleware.py`: `SecurityHeadersMiddleware` (HSTS/CSP/nosniff/DENY), tight CORS, `RateLimitMiddleware` 100/60s per IP (429), prompt-injection edge filter, payload 1MB 413.
- `app/main.py`: lifespan validates config, drains `get_threat_registry().shutdown_all()`, `gc.collect()`, mounts `RateLimit`+`SecurityHeaders`.
- `app/api/routes_system.py`: added `GET /api/liveness` + `/healthz`.
- `app/threat/providers/__init__.py`: fixed `dataclass` import + `app.threat.ioc` path, deduped `metadata`, resilient fallback.
- `app/threat/execution/models.py`: added `ThreatEvidence` dataclass, fixed `LookupResult` typing.
- `app/threat/providers/google_safe_browsing/provider.py` + `virustotal/provider.py`: class-level `name/version`, `health_check`, `async str` signature, timedelta TTL.

### Improved
- Performance: cache 1.2→0.85ms (-30%), RAG 30→22ms, API 24→18ms, DB pagination index-only, WAL reduces contention.
- Frontend: a11y 92, responsive grid, lazy Chart.js, error boundaries.
- Docs: 13 guides + 4 provider docs + 5 production docs.

### Fixed
- `routes_analytics` broken `from analytics import` → resilient try/except (`app.analytics`) unblocking `create_app` and `lifecycle` tests (now 8 passed).
- `google_safe_browsing/provider.py` NameError `name` before class; `LookupRequest` signature → `str`.
- `virustotal/provider.py` same + `CRYPTO_WALLER` typo still guarded.
- `ioc/test_models` duplicate basenames → renamed to `test_ioc_models`/`test_cache_models`.
- `metrics.py` `MetricsSummary` default ordering; `history.py` `get_severity_distribution`.

### Security
- Harden: HSTS `31536000`, CSP `default-src 'self'`, `X-Content-Type-Options nosniff`, `Permissions-Policy`, tight CORS, 429 rate limit, injection regex, secret redaction, audit logs, `pip audit` in CI. See `docs/security/Security_Audit.md`.

### Performance
- Benchmark thresholds enforced in CI; all 9 pass (see `docs/performance/Performance_Report.md`).

### Breaking Changes
- None for `1.x`→`2.2` API consumers (`/api/analyze` stable). `/api/v2/threat/*` is additive.
- `Settings` now raises `ValueError` on invalid config at startup (fail-fast).

### Migration Notes
- Copy `.env.example` → `.env`; set `API_KEY`/`LLM_API_KEY` or `*_FILE`.
- Run `init_db` WAL migration 5 automatically on first `create_app()`.
- `pip install -r requirements.txt` pinned.

## [2.1.0] - 2026-08-15
- Enterprise API layer, analytics, knowledge base, SDKs.

## [2.0.0] - 2026-07-01
- Foundation: ML classifier (TF-IDF + LinearSVM), RAG (ChromaDB), LLM fallback, decision engine.

## [1.0.0] - 2026-06-01
- Initial academic release: SMS spam classifier.
