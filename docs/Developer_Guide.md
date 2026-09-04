# Developer Guide — TextShield v2.2

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install black ruff mypy pytest pytest-cov
cp .env.example .env
```

## Project Structure
See `README.md#6` + `docs/architecture.md`.

## Running
- `python run.py` (FastAPI `create_app()` factory, dependency injection via `app/core/container.py`)
- `uvicorn app.main:app --reload`
- Tests: `pytest -q --cov=app`
- Lint: `scripts/lint.sh` (black --check, ruff, mypy, vulture)

## Conventions
- Branches `v2.2-dev` → `main`; conventional commits `feat(ioc): …`
- Module config via `app/core/settings.py` (`_get_secret`, `validate()`)
- Services in `app/services/`, logic not in routers; repositories in `app/database/repositories/`

## Adding Features
- New IOC extractor: implement `BaseExtractor` (`supports/extract/normalize/validate`) + register in `app/threat/ioc/registry.py`
- New provider: mirror `openphish/` (config/mapper/models/validator/client/provider) + `GET /api/v2/threat/providers/{name}`

## Debugging
- `LOG_FORMAT=json` for structured logs, `X-Request-ID` correlation, `app/observability/metrics.py`.

See `docs/setup.md`, `docs/Troubleshooting.md`, `docs/FAQ.md`.
