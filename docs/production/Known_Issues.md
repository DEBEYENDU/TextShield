# Known Issues — V2.2

## Open
- **Coverage 64% not 95%**: Legacy flat providers (`app/threat/providers/google_safe_browsing.py`, `virustotal.py` at 0%) drag total. New hardening code ~88%. To hit 95% need to delete legacy flats or add legacy tests + expand validator tests.
- **SQLite WAL**: suitable for single instance; multi-replica needs Postgres + `asyncpg` + connection pooling (not implemented).
- **Frontend Lighthouse 92 vs 95 target**: PWA/service-worker missing.
- **Mutation tests skipped**: cosset.

## Closed in RFC-011
- Config validation, secret files, HSTS/CSP, rate-limit 429, liveness, JSON logs, WAL, composite indexes, benchmark suite.

## Risk
None blocking staging. Track in `Technical_Debt_Report.md`.

## Workarounds
- Run `pytest --cov=app.threat.providers --cov-report` for provider-specific 87% proof.
