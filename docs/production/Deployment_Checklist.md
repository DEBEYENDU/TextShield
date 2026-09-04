# Deployment Checklist — V2.2

- [ ] `APP_ENV=production` + `LOG_FORMAT=json`
- [ ] Secrets via `*_FILE` (Docker/K8s secrets), not env plaintext; `API_KEY` + `LLM_API_KEY` set
- [ ] TLS termination (NGINX/ALB) + HSTS
- [ ] `pip install -r requirements.txt` pinned + `pip audit`
- [ ] `python -m benchmarks.suite --store --report` → no regressions
- [ ] `alembic` not used; `init_db` WAL verified; indexes applied (migration 5)
- [ ] `pytest -q` + `pytest --cov` ≥60% (target 95% — see Known Issues)
- [ ] Liveness `/api/liveness` + Readiness `/api/readiness` wired to k8s probes
- [ ] Resource limits: 1CPU/2GB, `gc.collect` on shutdown
- [ ] Log rotation 5MBx5 + ELK forward
- [ ] Backup `textshield.db` daily + `PRAGMA foreign_keys`
- [ ] Run `scripts/lint.sh`
