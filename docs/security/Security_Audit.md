# Security Audit — TextShield V2.2

**Date:** 2026-09-03 | **Env:** production hardening (RFC-011) | **Reviewer:** internal audit

## Scope
All subsystems: Auth, RBAC, secrets, config, API validation, input sanitization, output encoding, prompt injection, RAG poisoning, LLM validation, deps, CORS/CSRF, rate limiting, audit logs, headers, encryption.

## Findings & Hardening

### Authentication / Authorization / RBAC
- **Finding:** API was open; no auth layer.
- **Hardening:** `app/authentication/manager.py` enforces API-key header `X-API-Key` (optional in dev, required if `API_KEY` env set). RBAC stub `roles: admin/analyst/viewer` with `require_role` dependency. Tests in `tests/test_security.py`.

### Secrets Management
- **Finding:** Secrets via env only; no file support, no validation.
- **Hardening:** `app/core/settings.py` now supports `_get_secret` (env var or `*_FILE` Docker secret file). `load_settings()` validates required secrets at startup and fails fast. `.env.example` added. `HISTORY_STORE_PREVIEW` etc not secrets but bounded.

### Configuration
- Startup validation: `Settings.validate()` checks `DATABASE_URL` non-empty, `MAX_MESSAGE_LENGTH` range, `LLM_TIMEOUT_SECONDS`, etc. Called in `create_app` lifespan. Versioned via `CONFIG_VERSION=2.2`.

### API Validation
- All `routes_*` use Pydantic models with `Field(max_length=10000)` matching `MAX_MESSAGE_LENGTH`. Payloads >1MB rejected in `LoggingMiddleware` (413). Input sanitized: `html.escape` on output, URL validators in IOC extractors.

### Input Sanitization / Output Encoding
- User text truncated preview only in logs (hash, never raw). HTML templates use `| e` autoescape. JSON responses never reflect raw HTML.

### Prompt Injection Handling
- Edge regex `_INJECTION_PATTERNS` (`ignore previous instructions`, `system: you are`, `<|im_start|>`) flagged in `middleware.py`; suspicious payloads logged with `warning` and passed with `X-Injection-Flag` (not blocked outright to avoid false positives, but RAG+LLM layers strip instructions). `app/rag` sanitizes retrieved context with `strip_instructions`.
- LLM output validation: `app/rag` and `app/reasoning` validate JSON schema, truncate at token limit, reject if `explanation` contains disallowed content.

### RAG Poisoning Resistance
- KB entries require `source` whitelisting; ingestion via `routes_knowledge` validates `source` URL domain allowlist. Retrieval top-k bounded (`RAG_TOP_K=4`). Poisoning test: `tests/test_security.py::test_rag_poisoning_blocked`.

### Dependency Vulnerabilities
- `pip audit` / `safety` run in CI (`.github/workflows/ci.yml`). `requirements.txt` pinned. No known CVEs at audit (2026-09-03). `dependabot` enabled.

### CORS / CSRF
- `SecurityHeadersMiddleware` sets `Access-Control-Allow-Origin` only for localhost/https origins, `Vary: Origin`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `CSP: default-src 'self'`, `HSTS`.
- CSRF: API stateless (no cookies), so no CSRF token needed; `POST/PUT/DELETE` to `/api` require `Origin` or `X-Requested-With` if cookies were used (future-proof).

### Rate Limiting
- `RateLimitMiddleware` — 100 req/60s per IP sliding window, 429 with `Retry-After`, exempt health probes, headers `X-RateLimit-Limit/Remaining`. Provider-level `RateLimitManager` (threat) remains.

### Audit Logging
- `app/core/logging.py` structured format `timestamp | level | logger | request_id | msg`; `AuditService` (`app/analytics/audit.py`) writes to `system_logs` table with actor, action, resource, timestamp, IP, request_id. All `/api/analyze` and `/knowledge` mutations audit-logged.

### Secure Headers & Encryption
- HSTS `31536000; includeSubDomains`, CSP, nosniff. DB file chmod 600; SQLite `PRAGMA foreign_keys=ON`; at-rest encryption via filesystem (deployment checklist recommends LUKS). In-transit via TLS (deployment checklist). LLM API keys never logged; redacted via `redact_secrets`.

## Risk Matrix
| # | Risk | Before | After |
|---|---|---|---|
|1|No auth|High|Medium (API-key optional dev, enforced prod)|
|2|Secrets in logs|Medium|Low (redaction)|
|3|Prompt injection|High|Medium (defense-in-depth)|
|4|Rate limit bypass|Medium|Low (double layer)|
|5|CORS wildcard|Low|Low (tightened)|

## Recommendations
- Enable mTLS for inter-service if microservices.
- Rotate `API_KEY` via secret file every 90d.
- Add WAF in front of FastAPI (NGINX).

## Tests
`tests/test_security.py` (18 tests), `tests/test_hardening.py` (probes, headers).
