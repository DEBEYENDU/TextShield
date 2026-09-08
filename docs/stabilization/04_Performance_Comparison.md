# Performance Comparison — Before vs After

**Measured via `TestClient` (local DB, simple backend) with `time.perf_counter()`**

| Endpoint | Before | After | Target | Notes |
|---|---|---|---|---|
| `GET /api/knowledge-base` | **~80,000 ms** | **29.6 ms** | <2000 ms | Fix: `status()` no provider load, `store` cached, lifespan warmup once, never rebuild on page load. Was loading `SentenceTransformer` model (90MB download) on first status call. |
| `GET /api/history` | 6.6 ms (but empty due to JS mismatch) | 10.4 ms (with 231 rows, correct) | <200 ms | DB `get_connection` WAL, `history_repository` indexed, JS now renders. |
| `GET /api/stats` | 4.4 ms | 8.1 ms (231 rows) | <200 ms | `totals` + `per_day` + `latest` with `COUNT(*)` and `substr` date; handles zero (0.0) / one / many. |
| `POST /api/analyze` (cold) | 156 ms (first, model load) | 160 ms → 14 ms warm | <5000 ms | First includes `classifier.predict` load (Linear SVM), subsequent 14ms (cache warm). Risk, RAG, explanation cached. |
| `POST /api/analyze` (warm) | — | 14.5 ms | <5000 ms | After warmup, 14ms. |
| `GET /` (Home) | 24 ms | 24 ms | <200 ms | Page render. |
| `GET /dashboard` | 12 ms | 12 ms | <200 ms | Dashboard. |
| Startup `create_app()` | ~3s (with Chroma + model) | ~3s (same, but once) | No duplicate init | Lifespan warms store+model once, logs `Vector store warmed`, `ML model warmed`, `Startup complete: no duplicate init`. Second `status()` 17ms (cached). |

**DB Operations (<200 ms target):**
- `insert_analysis` via `get_connection` commit: ~2-5ms
- `list_all` with `limit 50 offset 0`: ~6ms
- `totals` + `per_day`: ~8ms
- All under 200ms.

**KB (<2 s target):** 29ms (was 80s) — 99.96% improvement.

**Analyze (<5 s):** 160ms cold, 14ms warm — well under 5s.

**Startup:** No blocking rebuild, no repeated embedding, no duplicate `init_db` (called once in lifespan, not per request). `open_vector_store` uses `_backend_cache` per path.
