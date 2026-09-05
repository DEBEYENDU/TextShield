# Configuration — TextShield v2.2

**Version:** `2.2.0` | **Canonical source:** `app/core/settings.py` `Settings` + shim `app/core/config.py`

## Architecture
```
.env + env vars (+ *_FILE secrets)  -->  dotenv.load_dotenv  -->  Settings class (typed, validated)  -->  app.core.config shim  -->  consumers (run.py, main.py, database, ML, RAG, Threat, Dashboard, workers)
                |                                                        |
                +-- app/rag/config.RagConfig.from_settings() reads Settings.RAG_* if present
                +-- app/threat providers read Settings via manager
```

- **Single source of truth:** `Settings` in `app/core/settings.py`. No duplicated configuration; `app/rag/config.py` only holds defaults and overrides from `Settings` via `from_settings()`. `app/core/config.py` is a deprecated shim re-exporting `Settings` for old imports.
- **Strong typing:** Every field annotated (`str`, `int`, `float`, `bool`, `Path`, `dict`), IDE-friendly, `pyproject.toml` `mypy` checks.
- **Secrets:** `_get_secret` checks `<KEY>_FILE` first (Docker secret), then env var. Never logged.
- **Loading:** `BASE_DIR = Path(__file__).parent.parent.parent`, `load_dotenv(BASE_DIR / ".env")` at import, helpers `_get`, `_get_bool`, `_get_int`, `_get_float`, `_get_secret`.

## Environment Variables

| Variable | Attribute | Default | Description |
|---|---|---|---|
| `APP_ENV` | `ENVIRONMENT` | `development` | `development|staging|production|test` (canonical, `APP_ENV` alias deprecated) |
| `APP_HOST` | `APP_HOST` | `127.0.0.1` | Bind host |
| `APP_PORT` | `APP_PORT` | `8000` | Bind port |
| `APP_TITLE` | `APP_TITLE` | `TextShield` | UI title |
| `DATABASE_URL` | `DATABASE_URL` | `sqlite:///./textshield.db` | SQLite URL |
| `API_KEY` / `API_KEY_FILE` | `API_KEY` | `""` | Optional in dev, enforce in prod |
| `ALLOWED_ORIGINS` | `ALLOWED_ORIGINS` | `http://localhost:8000,...` | CORS |
| `JWT_SECRET_KEY` / `*_FILE` | `JWT_SECRET_KEY` (`jwt_secret_key`) | `change-me-...` | JWT HMAC |
| `JWT_ALGORITHM` | `JWT_ALGORITHM` (`jwt_algorithm`) | `HS256` | JWT alg |
| `JWT_EXPIRATION_MINUTES` | `JWT_EXPIRATION_MINUTES` (`jwt_expiration_minutes`) | `60` | JWT TTL |
| `HISTORY_STORE_PREVIEW` | `HISTORY_STORE_PREVIEW` | `false` | Store message preview |
| `HISTORY_PREVIEW_LENGTH` | `HISTORY_PREVIEW_LENGTH` | `120` |  |
| `MAX_MESSAGE_LENGTH` | `MAX_MESSAGE_LENGTH` | `10000` | Validation 1..100000 |
| `MODEL_PATH` | `MODEL_PATH` | `models/spam_classifier.joblib` |  |
| `VECTORIZER_PATH` | `VECTORIZER_PATH` | `models/tfidf_vectorizer.joblib` |  |
| `MODEL_METADATA_PATH` | `MODEL_METADATA_PATH` | `models/model_metadata.json` |  |
| `MODEL_METRICS_PATH` | `MODEL_METRICS_PATH` | `models/evaluation_report.json` |  |
| `VECTOR_DB_PATH` | `VECTOR_DB_PATH` | `vector_db` |  |
| `RAG_TOP_K` | `RAG_TOP_K` | `4` | 1..20 |
| `RAG_MAX_CONTEXT_CHUNKS` | `RAG_MAX_CONTEXT_CHUNKS` | `5` | RagConfig override |
| `RAG_MAX_TOKEN_LIMIT` | `RAG_MAX_TOKEN_LIMIT` | `2000` |  |
| `RAG_SIMILARITY_THRESHOLD` | `RAG_SIMILARITY_THRESHOLD` | `0.35` |  |
| `EMBEDDING_PROVIDER` | `EMBEDDING_PROVIDER` | `sentence_transformers` |  |
| `EMBEDDING_MODEL` | `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |  |
| `SEMANTIC_ENABLED` | `SEMANTIC_ENABLED` | `true` |  |
| `SEMANTIC_EMBEDDING_MODEL` | `SEMANTIC_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` |  |
| `SEMANTIC_EMBEDDING_DIMENSION` | `SEMANTIC_EMBEDDING_DIMENSION` | `384` |  |
| `SEMANTIC_CACHE_SIZE` | `SEMANTIC_CACHE_SIZE` | `512` |  |
| `SEMANTIC_BATCH_SIZE` | `SEMANTIC_BATCH_SIZE` | `16` |  |
| `SEMANTIC_DEVICE` | `SEMANTIC_DEVICE` | `auto` |  |
| `SEMANTIC_LANGUAGE_DETECTION` | `SEMANTIC_LANGUAGE_DETECTION` | `auto` |  |
| `INTENT_ENABLED` | `INTENT_ENABLED` | `true` |  |
| `INTENT_CONFIDENCE_THRESHOLD` | `INTENT_CONFIDENCE_THRESHOLD` | `0.35` |  |
| `INTENT_BEHAVIOR_THRESHOLD` | `INTENT_BEHAVIOR_THRESHOLD` | `0.30` |  |
| `INTENT_URGENCY_THRESHOLD` | `INTENT_URGENCY_THRESHOLD` | `0.30` |  |
| `INTENT_MAX_INTENTS` | `INTENT_MAX_INTENTS` | `4` |  |
| `LLM_PROVIDER` | `LLM_PROVIDER` | `ollama` | `ollama|openai|nvidia|none` |
| `LLM_MODEL` | `LLM_MODEL` | `""` |  |
| `LLM_BASE_URL` | `LLM_BASE_URL` | `http://localhost:11434` |  |
| `LLM_API_KEY` / `*_FILE` | `LLM_API_KEY` | `""` |  |
| `LLM_TIMEOUT_SECONDS` | `LLM_TIMEOUT_SECONDS` | `30` | 1..300 |
| `LLM_TEMPERATURE` | `LLM_TEMPERATURE` | `0.2` |  |
| `RISK_SPAM_BASE` | `RISK_SPAM_BASE` | `50.0` |  |
| `RISK_HAM_BASE` | `RISK_HAM_BASE` | `5.0` |  |
| `RISK_INDICATOR_HIGH_WEIGHT` | `RISK_INDICATOR_WEIGHTS.high` | `12.0` |  |
| `RISK_INDICATOR_MEDIUM_WEIGHT` | `RISK_INDICATOR_WEIGHTS.medium` | `7.0` |  |
| `RISK_INDICATOR_LOW_WEIGHT` | `RISK_INDICATOR_WEIGHTS.low` | `3.0` |  |
| `RISK_URL_HIGH_PATTERN` | `RISK_URL_HIGH_PATTERN` | `10.0` |  |
| `RISK_URL_SUSPICIOUS` | `RISK_URL_SUSPICIOUS` | `6.0` |  |
| `RISK_URL_SHORTENER` | `RISK_URL_SHORTENER` | `4.0` |  |
| `RISK_HIGH_CONF_BONUS` | `RISK_HIGH_CONF_BONUS` | `15.0` |  |
| `RISK_RAG_CATEGORY_BONUS` | `RISK_RAG_CATEGORY_BONUS` | `8.0` |  |
| `RISK_INTENT_MALICIOUS` | `RISK_INTENT_MALICIOUS` | `12.0` |  |
| `RISK_MEDIUM_THRESHOLD` | `RISK_MEDIUM_THRESHOLD` | `30.0` |  |
| `RISK_HIGH_THRESHOLD` | `RISK_HIGH_THRESHOLD` | `60.0` |  |
| `RISK_CRITICAL_THRESHOLD` | `RISK_CRITICAL_THRESHOLD` | `80.0` |  |
| `RISK_CRITICAL_CONFIDENCE` | `RISK_CRITICAL_CONFIDENCE` | `0.85` |  |
| `RISK_UNCERTAIN_CONFIDENCE` | `RISK_UNCERTAIN_CONFIDENCE` | `0.5` |  |
| `FEATURE_RAG` | `FEATURE_RAG` | `true` |  |
| `FEATURE_LLM` | `FEATURE_LLM` | `true` |  |
| `FEATURE_HISTORY` | `FEATURE_HISTORY` | `true` |  |
| `CONFIG_VERSION` | `CONFIG_VERSION` | `2.2.0` |  |
| `LOG_FORMAT` | (logging) | `text` | `text|json` |

Full file: `.env.example` (88 lines with comments).

## Configuration Loading
1. `dotenv.load_dotenv(BASE_DIR / ".env")` at import.
2. Helpers read env/concurrent `*_FILE` via `_get_secret`.
3. `Settings` class vars evaluated at import (env snapshot); instance `settings = Settings()` + `ensure_directories()`.
4. Consumers `from app.core.settings import settings` or `from app.core.config import settings` (shim).
5. `app/rag/config.RagConfig.from_settings(Settings)` merges central values + module defaults.

## Validation
`Settings.validate() -> list[str]` called in `load_settings()` and `app/main.py` lifespan (fail-fast `RuntimeError` if errors, `ValueError` in `load_settings`). Checks:
- `DATABASE_URL` non-empty
- `MAX_MESSAGE_LENGTH 1..100000`
- `LLM_TIMEOUT_SECONDS 1..300`
- `RAG_TOP_K 1..20`
- `RISK thresholds: medium < high < critical`
- `ENVIRONMENT in {development,staging,production,test}`

New JWT/RAG fields use sensible defaults, no extra validation needed (HS256 always valid).

## Development Mode
- `APP_ENV=development` → `uvicorn reload` (`run.py`), verbose logs, `API_KEY` optional, SQLite `textshield.db` in repo, `LOG_FORMAT=text`, template LLM fallback.

## Production Mode
- `APP_ENV=production`, `LOG_FORMAT=json`, `JWT_SECRET_KEY` (via `*_FILE` `/run/secrets/jwt`, 64+ chars, rotate 90d), `API_KEY` required, `DATABASE_URL` maybe Postgres (future), TLS via NGINX, `CONFIG_VERSION` logged at startup, `HSTS` headers, `RateLimit 100/60s`.

Example `.env.production`:
```
APP_ENV=production
APP_HOST=0.0.0.0
DATABASE_URL=sqlite:///./textshield.db
JWT_SECRET_KEY_FILE=/run/secrets/jwt
API_KEY_FILE=/run/secrets/api_key
LOG_FORMAT=json
```

## Examples
```bash
cp .env.example .env
# edit LLM_PROVIDER, API keys
python run.py  # reload if ENVIRONMENT==development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # alt
```

Programmatic:
```python
from app.core.settings import settings, load_settings
s = load_settings()  # validates + ensures dirs
print(s.ENVIRONMENT, s.APP_ENV)  # APP_ENV alias works
```

## Migration Notes
- **Renamed:** `APP_ENV` (attribute) → `ENVIRONMENT` (canonical). Env var name stays `APP_ENV`. `Settings.APP_ENV` kept as `@property` alias (getter+setter) for backward compat; new code must use `settings.ENVIRONMENT`. `run.py` updated `settings.APP_ENV` → `settings.ENVIRONMENT`.
- **Added:** `JWT_SECRET_KEY`/`JWT_ALGORITHM`/`JWT_EXPIRATION_MINUTES` (previously missing, caused `AttributeError` in `authentication/manager.py`), `RAG_MAX_CONTEXT_CHUNKS`/`RAG_MAX_TOKEN_LIMIT`/`RAG_SIMILARITY_THRESHOLD` (centralized, previously only in `app/rag/config.py` defaults).
- **Deprecated:** None removed; `app/core/config.py` shim kept for `from app.core.config import settings` imports but marked deprecated — new code import from `app.core.settings`.
- **Duplicate removed:** `RAG_TOP_K` etc previously duplicated between `Settings` and `RagConfig` defaults; now `Settings` is single source, `RagConfig.from_settings` overrides only if `hasattr` present.
- **Unused:** `SEMANTIC_ENABLED`, `INTENT_ENABLED`, `FEATURE_*` are checked via `app/core/features.py` not directly; still validated but not flagged as unused — intentional feature flags.
- **Incorrect defaults fixed:** `RISK` thresholds ordering now validated; `JWT_EXPIRATION_MINUTES` default 60 (was missing → crash), `RAG_SIMILARITY_THRESHOLD` 0.35 matches `RagConfig`.

See `CHANGELOG.md` + `docs/MIGRATION_GUIDE.md`.
