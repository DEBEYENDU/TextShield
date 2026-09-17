# Troubleshooting — TextShield v2.2

## Install
- `chromadb` fails → app falls back to hashing embedder + numpy store; still works.

## Model
- `spam_classifier.joblib` missing → run `python scripts/train_model.py`; check `models/model_metadata.json`.

## RAG
- `vector_db` empty → `python scripts/build_knowledge_base.py`; check `logs/textshield.log`.

## LLM
- Ollama unreachable → set `LLM_PROVIDER=none` for template fallback; check `LLM_BASE_URL`/`API_KEY`.

## DB
- `database locked` → `PRAGMA journal_mode=WAL` (migration 5); ensure no second writer; `PRAGMA busy_timeout 5000`.

## Threat
- Provider returns None → check `API_KEY`, `health` via `GET /api/v2/threat/providers/openphish`, `health_check()`.

## Config
- `Invalid configuration` at startup → read error list, fix `.env`; `CONFIG_VERSION` mismatch.

## Performance
- Cold start 2741ms single_message → warm 42ms after cache; run `python -m benchmarks.suite --iterations 20`.

## Tests
- `ModuleNotFoundError: analytics` → fixed in `routes_analytics` try/except; `knowledge_loader` error is pre-existing (use `app/rag` paths).

See `docs/setup.md`, `docs/FAQ.md`.
