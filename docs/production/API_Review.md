# API Review — V2.2

## Endpoints Audited
`/api/health`, `/readiness`, `/liveness`, `/healthz`, `/version`, `/config/status`, `/status`, `/api/analyze` (rate-limited), `/api/knowledge/*`, `/api/history`, `/v2/threat/*`, `/api/v2/threat/providers/*`, `/dashboard/*`.

## Consistency
- All JSON responses use `{status, data, error}` envelope via `app/core/errors.py` (except legacy). Status codes: 200 OK, 201 Created, 400 Validation, 404 Not Found, 413 Payload Too Large, 429 Rate Limited, 500 Exception boundary.
- Pagination: `skip/limit` or `page/page_size` with `total` + `total_pages` (e.g., `/dashboard/history?page=1&page_size=10`).
- Versioning: `/api` (v2.0) + `/v2` + `/api/v2` (threat) — documented; future uses `Accept: application/vnd.textshield.v3+json`.

## Validation & Error Handling
- Pydantic `Field(max_length=10000)` enforced; `get_connection` rollback + `register_exception_handlers` catches `ValidationError` → 400, `HTTPException` → as-is, generic → 500 with `request_id`.
- Provider 404 for unknown provider; rate-limit 429 JSON.

## Auth
- `X-API-Key` checked in `authentication/manager.py` if `API_KEY` set; otherwise open in dev. RBAC stub `require_role`.

## Docs
- OpenAPI at `/docs` (FastAPI auto). Added `docs/api.md` with curl examples.

## Recommendations
- Add `ETag` for `/api/history` caching.
