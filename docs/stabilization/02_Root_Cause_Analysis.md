# Root Cause Analysis

## 1. Analyze Workflow — No Request / No Render / Not Persisted
- **Frontend Validation:** `required` on hidden textareas → browser `:invalid` prevented `submit` event from firing. No JS, no fetch, no log. **Fix:** `novalidate` + remove `required`, JS validation.
- **JS Namespace:** `const { escapeHtml } = window.textshield` threw before `fetch` → uncaught, spinner stuck, no request. **Fix:** defensive.
- **Backend:** Missing logs made silent failures invisible; history `per_day` brittleness masked DB save verification. **Fix:** detailed logs, DB test fix.
- **Render:** `renderResult` assumed `data.indicators` etc always array; if `null` → `TypeError` and no render. **Fix:** `data.indicators || []`.

## 2. History Empty
- **Wrong Table Queried:** No — DB insert worked (`db.insert_analysis` commits). `GET /api/history` returned 231 rows in test, so data *was* saved.
- **Wrong API Used:** No — `/api/history` correct, but JS expected `data.success` + `data.data` (old `app/static` style) vs actual `{items,total,limit,offset}` → `render` received `undefined` → no rows.
- **Frontend Rendering:** `history-body` vs `history-table-body` mismatch → `tbody` null → early return → empty table forever. No error shown because catch swallowed.

## 3. Analytics JS Errors
- **Missing DOM:** `analytics.js` queried `stat-total` etc not in `analytics.html` (has `analytics-stats` + 7 canvases). `null.textContent` → TypeError.
- **Incorrect Selectors:** `chart-risk` vs `chart-risk-distribution` etc.
- **API Mismatch:** Actually correct (`/api/stats` returns `total_analyses` etc) but JS expected `stats.total` → undefined → `NaN%`.
- **Chart Rendering:** `drawDonut` with `total=0` did `r * 0` → invisible, no fallback.

## 4. Knowledge Base 80s
- **Chroma Init:** `ChromaVectorStore._load` → `chromadb.PersistentClient` opens DB, but first `retriever.status()` also called `self.provider.name` → `create_embedding_provider` → `SentenceTransformer("all-MiniLM-L6-v2")` → if model not cached, download 90MB → 80s blocking the request thread (synchronous). No cache, no warmup, repeated per request (though cached after first, first hit still 80s).
- **Repeated Embedding:** Not repeated, but first hit blocked.
- **Rebuild:** Not on page load, but `status()` slowness made it appear as infinite loading (spinner never cleared because `fetch` took 80s).

## 5. JS Integration
- **Global Namespace:** Canonical `window.textshield` defined only in `common.js`, but `common.js` loaded *after* page scripts → `undefined` at parse time. Destructuring threw before DOMContentLoaded.
- **Imports:** `app/static/js/knowledge.js` had syntax error `) const` → parse error → no `initKnowledgeExplorer` → infinite loading.

## 6. FastAPI
- **Request Schema:** Correct (`AnalyzeRequest`), but `HistoryFilters` vs `limit/offset` mismatch in old JS.
- **Response Schema:** `AnalysisResult` always returned, but `HistoryResponse` vs `data.success` mismatch.
- **Exception Handling:** `analysis_service` swallowed history errors but logged, correct.
- **Serialization:** `HistoryEntry.model_dump()` ok.

## 7. Database
- **Analysis Table:** `analyses` ok, `init_db` WAL, `history_repository.create` commits.
- **History Query:** `list_all` with `order_by` whitelist ok.
- **Analytics:** `per_day` brittle date compare vs hardcoded test data.

## 8. Performance
- **KB:** 80s due to model download on first `status()` call, no warmup, no cache. Fixed: status no longer loads model, lifespan warms store once (29ms).
- **History/Analytics:** 6-10ms (fast), Analyze 14-160ms (under 5s).

## 9. Logging
- **Backend:** Only `analyze requested` and `analysis complete` logged; missing 5 stages. Fixed.
- **Frontend:** No `console.log` for request/response/error → silent. Fixed.

## 10. Browser
- Console showed `Uncaught TypeError: Cannot destructure...`, `showToast is not defined`, `knowledge.js:61 SyntaxError`. All fixed.
