# Deployment Guide — TextShield v2.2

## Local
`python run.py` → `http://127.0.0.1:8000`; `/docs` Swagger.

## Docker (if added)
`docker compose up --build` (FastAPI + volumes `vector_db/`, `textshield.db`, `logs/`).

## Production Checklist
See `docs/production/Deployment_Checklist.md` + `Production_Readiness_Checklist.md`.

## Probes
K8s: `livenessProbe` `/api/liveness` (process alive), `readinessProbe` `/api/readiness` (DB+migrations+model), `healthz` `/api/healthz`.

## Secrets
Mount `API_KEY_FILE`/`LLM_API_KEY_FILE` at `/run/secrets/*`, set `APP_ENV=production`, `LOG_FORMAT=json`, TLS via NGINX/ALB, `HSTS`.

## DB
SQLite WAL (migration 5 indexes) single instance; for HA use Postgres + `asyncpg` (future v2.3).

## Scaling
`max_concurrency 10` (`app/threat/execution/executor.py`), `RateLimit 100/60s` per IP, provider `burst` limits.

## Backup
Daily `textshield.db` dump + `PRAGMA foreign_keys`; logs 5MBx5 rotation → ELK.

## CI
`.github/workflows/ci.yml` runs black, ruff, mypy, pytest --cov, benchmark, pip-audit, docs validation on `v2.2-dev`/`main`.
