# Migration Guide — 2.1.0 → 2.2.0

## Overview
2.2.0 is additive; no breaking API for `1.x`/`2.1` consumers. `/api/analyze` stable.

## Steps
1. `git pull origin v2.2-dev` or download `v2.2.0` tag tarball.
2. `cp .env.example .env` (new vars: `API_KEY`/`*_FILE`, `LOG_FORMAT`, `CONFIG_VERSION=2.2.0` auto, threat provider keys optional).
3. `pip install -r requirements.txt` (pinned).
4. `python run.py` → `init_db` auto-applies migration 5 (composite indexes + WAL). No manual `alembic`.
5. Rebuild KB optional: `python scripts/build_knowledge_base.py` (persistent `vector_db/`).

## DB
SQLite `PRAGMA journal_mode=WAL` set on connect; first run converts. For Postgres HA, manual migration needed (future v2.3).

## Config
- If `API_KEY` set, clients must send `X-API-Key`; dev without key stays open.
- `*_FILE` secrets: set `API_KEY_FILE=/run/secrets/api_key` instead of `API_KEY`.

## Tests
`pytest -q --ignore=tests/test_knowledge_base.py` should pass 168+. Run `benchmarks/suite.py`.

## Rollback
Downgrade `app/__init__.py` to `2.1.0`, remove migration 5 entry from `schema_migrations` (or restore `textshield.db` backup), reinstall `2.1` requirements.

## Breaking
- `Settings.validate()` now fail-fast on invalid config (previously silent). Fix `.env` errors shown in log.
