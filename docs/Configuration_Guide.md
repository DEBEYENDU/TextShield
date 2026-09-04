# Configuration Guide — TextShield v2.2

All via `app/core/settings.py` (env + `*_FILE` Docker secrets) + `.env.example`.

## Core
`APP_ENV` (development|staging|production|test), `APP_HOST`, `APP_PORT`, `APP_TITLE`, `DATABASE_URL` (`sqlite:///./textshield.db`), `CONFIG_VERSION=2.2.0`.

## Limits
`MAX_MESSAGE_LENGTH=10000`, `RAG_TOP_K=4`, `HISTORY_STORE_PREVIEW`, `HISTORY_PREVIEW_LENGTH`.

## Paths
`MODEL_PATH`, `VECTORIZER_PATH`, `MODEL_METADATA_PATH`, `MODEL_METRICS_PATH`, `VECTOR_DB_PATH`.

## Providers
`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `SEMANTIC_*`, `INTENT_*`, `LLM_PROVIDER` (ollama|openai|nvidia|none), `LLM_MODEL/BASE_URL/API_KEY/TIMEOUT/TEMPERATURE`.

## Risk
`RISK_SPAM_BASE`, `RISK_HAM_BASE`, `RISK_INDICATOR_WEIGHTS`, `RISK_URL_*`, `RISK_*_THRESHOLD` (medium < high < critical enforced in `validate()`).

## Feature Flags
`FEATURE_RAG`, `FEATURE_LLM`, `FEATURE_HISTORY`.

## Security
`API_KEY`/`API_KEY_FILE`, `ALLOWED_ORIGINS`, `LLM_API_KEY`/`*_FILE`, `LOG_FORMAT` (text|json).

## Validation
`Settings.validate()` checks `DATABASE_URL` non-empty, `MAX_MESSAGE_LENGTH 1..100000`, `LLM_TIMEOUT 1..300`, `RAG_TOP_K 1..20`, threshold ordering, env enum. Called at startup (`lifespan`) — fail-fast `ValueError`.

See `docs/setup.md`, `.env.example`.
