# Release Notes — TextShield v2.2.0 (2026-09-03)

## Highlights
Production-ready threat intelligence platform + hardening + release prep.

## Added
- 6 threat providers (GSB, VT, OpenPhish, PhishTank, URLhaus, AbuseIPDB) with cache/retry/rate-limit/circuit-breaker, normalized `ThreatEvidence`, `GET /api/v2/threat/providers/*`.
- IOC extraction (7 types) + Threat Cache + Async Lookup + Aggregation + Unified Evidence + Dashboard (11 panels, Chart.js).
- Benchmark suite (9 targets, history, report), observability metrics, JSON logs, `X-Request-ID`+`traceparent`.
- Examples (Python/JS/cURL/batch/webhook/plugin), 13 guides, 8 Mermaid diagrams.

## Improved
- Cache 30% faster, WAL+indexes, API 18ms, RAG 22ms.
- Security headers (HSTS/CSP), tight CORS, 429, injection filter, secret files.
- Resilience: graceful shutdown drain+gc, liveness/readiness/healthz.

## Fixed
- `routes_analytics` import, provider NameErrors, validator duplicates.

## Security
See `docs/security/Security_Audit.md`; `pip audit` in CI.

## Performance
All 9 benchmarks pass (see `benchmarks/report.json`).

## Migration
See `docs/MIGRATION_GUIDE.md`; no breaking API.

## Contributors
Debeyendu Nirmal Karmakar + open-source libs.

## Artifacts
Tag `v2.2.0`, `CHANGELOG.md`, `docs/Release_Checklist.md`.
