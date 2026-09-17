# Contributing to TextShield

Thank you for your interest in contributing to TextShield! This project is an academic, production-quality spam/ham detection platform with RAG and Threat Intelligence.

## Code of Conduct

By participating, you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the Bug Report template
3. Provide steps to reproduce, expected vs actual behavior, environment details

### Suggesting Enhancements

1. Open an issue with Feature Request template
2. Describe the problem and proposed solution

### Pull Requests

1. Fork the repo and create a feature branch from `v2.2-dev`
2. Keep changes focused and small
3. Add tests for new functionality
4. Ensure `black`, `ruff`, `mypy`, `pytest` pass
5. Update docs if needed
6. Follow Conventional Commits

Branch naming: `feat/<short-desc>`, `fix/<short-desc>`, `docs/<short-desc>`

Commit examples:
```
feat(api): add v2 batch endpoint
fix(frontend): handle empty history state
test(ioc): add extraction coverage
docs(readme): improve quick start
```

### Development Setup

```bash
git clone https://github.com/DEBEYENDU/TextShield.git
cd TextShield
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/prepare_dataset.py
python scripts/train_model.py
python scripts/build_knowledge_base.py
python run.py
```

Run tests:
```bash
pytest -q
```

Lint:
```bash
black app tests benchmarks
ruff check app tests
mypy app --ignore-missing-imports
```

## Project Structure

See README.md Section 6.

## Review Process

PRs target `v2.2-dev`. CI must pass. Maintainers review for correctness, tests, and docs.

## Questions?

Open a Discussion or issue with type "Question".

Thank you!
