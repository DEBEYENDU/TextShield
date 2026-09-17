# Release Checklist — v2.2.0

- [x] Version bump `app/__init__ 1.0.0→2.2.0`, `pyproject [project]`, `frontend/package.json`, `CONFIG_VERSION 2.2.0`
- [x] CHANGELOG.md Keep a Changelog updated
- [x] README reviewed (40 sections incl. Quick Start, SDKs, Threat/RAG/Decision/Evidence)
- [x] Docs verified: Developer, Configuration, Deployment, Threat, Evidence, Plugin, Troubleshooting, FAQ, Architecture Diagrams
- [x] Examples: Python/JS/cURL/batch/webhook/plugin in `examples/`
- [x] Installation verified (`pip install -r requirements`, `prepare_dataset`, `train_model`, `build_knowledge_base`)
- [x] Tests verified: `pytest --ignore=test_knowledge_base -q` 168+ passed, lifecycle 8 passed, perf/hardening 28 passed
- [x] Performance verified: `benchmarks/suite --store --report` 9/9 pass, history 1 entry
- [x] Security verified: headers, CORS tight, 429, injection, secrets `_FILE`, audit logs → `docs/security/Security_Audit.md`
- [x] Documentation verified: 13 guides + provider + production docs
- [x] API verified: `/api/health|readiness|liveness|version`, `/api/v2/threat/providers/*`, `/dashboard/*`
- [x] DB migrations verified: migration 5 indexes, WAL, `init_db` idempotent
- [x] Env vars documented in `.env.example`
- [x] Code review: TODOs scanned, dead code check via vulture, duplicate `google_safe_browsing.py` noted (legacy, keep for compat)
- [x] Quality gates: `pyproject.toml` black/ruff/mypy/coverage, `scripts/lint.sh`, CI `.github/workflows/ci.yml`
- [x] Release tag ready: `v2.2.0` (to be created after validation)
