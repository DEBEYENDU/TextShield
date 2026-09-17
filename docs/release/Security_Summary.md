# Security Summary — v2.2.0

Covers `docs/security/Security_Audit.md` audit 2026-09-03.

- Headers: HSTS 31536000, CSP default-src self, nosniff, DENY, Referrer strict-origin, Permissions-Policy.
- CORS tight (localhost/https only, Vary Origin), no wildcard.
- Rate limit 100/60s IP + provider burst, 429 JSON.
- Injection filter 3 regex + RAG strip + LLM validation.
- Secrets via `*_FILE` + redaction + audit logs.
- Validation: Pydantic max_length 10000, payload 1MB 413, URL validators.
- DB PRAGMA foreign_keys, file 600, WAL.
- CI: pip-audit, dependabot, TLS in checklist.

Risk matrix improved High→Medium/Low. Recommendation: mTLS, rotation 90d, WAF.

Tests: `tests/test_security.py` 8 passed.
