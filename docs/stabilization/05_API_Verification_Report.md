# API Verification Report

**Tool:** `TestClient(create_app())` (FastAPI) | **Date:** 2026-09-08

| Endpoint | Method | Request Schema | Response Schema | Status | DB Commit | Serialization |
|---|---|---|---|---|---|---|
| `POST /api/analyze` | POST | `AnalyzeRequest` (`input_type` literal sms/text/email, `message`/`subject`/`sender`/`body`/`email_raw`, `model_validator` ensures one of message/body/email_raw) | `AnalysisResult` (`classification`, `confidence`, `risk_score`, `risk_level`, `message_type`, `intent`, `indicators`, `urls`, `rag_evidence`, `explanation`, `explanation_source`, `recommended_action`, `risk_factors`, `model_used`, `rag_status`) | 200 OK, 422 validation (`ValueError` → `ValidationAppError`), 503 if model missing, 500 `AppError` logged | Yes: `db.insert_analysis` via `get_connection` commit, `history` row hashed, `preview` optional | `HistoryEntry.model_dump()` |
| `GET /api/history` | GET | Query `input_type?, classification?, risk_level?, intent?, limit 1..200, offset, order_by in {timestamp,id,confidence,...}, direction asc/desc` (`HistoryFilters`) | `{items: [HistoryEntry], total, limit, offset}` | 200, 422 if invalid literal | Read via `history_repository.list_all` + `count` | `HistoryEntry` |
| `DELETE /api/history/{id}` | DELETE | `entry_id: int` | `{"deleted": True, "id": int}` or 404 | 200, 404 `NotFoundError` | Yes: `delete_by_id` commit | — |
| `DELETE /api/history` | DELETE | — | `{"deleted": True, "rows_deleted": int}` | 200 | Yes: `clear` commit | — |
| `GET /api/stats` | GET | — | `StatsResponse` (`total_analyses`, `spam_count`, `ham_count`, `spam_percentage`, `average_confidence`, `risk_distribution`, `message_type_distribution`, `intent_distribution`, `analyses_per_day`, `latest_analysis_at`) | 200 | Read `totals` + `per_day` + `latest_timestamp` | — |
| `GET /api/model-info` | GET | — | `ModelInfoResponse` (`available`, `algorithm`, `trained_at`, `metrics`, `comparison`) | 200 | Read `model_metadata.json` | — |
| `GET /api/knowledge-base` | GET | — | `{ready, backend, embedding_provider, chunk_count, document_count, categories, built_at}` | 200 (<30ms) | Read `structure.json` (no DB) | — |
| `POST /api/knowledge-base/rebuild` | POST | — | Same as status but with `ready True` after `scripts/build_knowledge_base.build()` + `retriever.invalidate_cache()` | 200, 500 `KnowledgeBaseError` | `retriever.invalidate_cache()` | — |
| `GET /api/health` | GET | — | `HealthResponse` (`status`, `version`, `model_ready`, etc) | 200 | — | — |
| `GET /api/readiness` | GET | — | `ReadinessResponse` | 200 | Checks DB `init_db` | — |
| `GET /api/liveness` | GET | — | `{status: "alive", checks: {process:"ok"}}` | 200 | No dep checks (k8s) | — |
| `GET /api/healthz` | GET | — | `{ok: True}` | 200 | — | — |
| `GET /api/version` | GET | — | `{name, version, tagline, environment}` | 200 | — | — |
| `GET /` etc (pages) | GET | — | HTML (Jinja) | 200 | — | — |

**Exception Handling:** `register_exception_handlers` catches `ValidationAppError` → 422, `ServiceUnavailableError` → 503, `AppError` → 500 with `request_id`, generic → 500 logged.

**Transactions:** `get_connection` context manager `commit` on exit, `rollback` on exception, `RLock` for SQLite writes, `WAL` + `busy_timeout 5000`.

**Serialization:** All `HistoryEntry`, `AnalysisResult` via `model_dump()`, `row` via `dict(row)`, `json` dumps via `response.json()`.

**Docs Match:** `GET /docs` OpenAPI matches `AnalyzeRequest`/`AnalysisResult`/`HistoryResponse` etc; `GET /api/knowledge-base` now <2s, matches frontend `fetch("/api/knowledge-base")` (kb.js) which expects `ready, backend, chunk_count` etc — verified.
