# FAQ — TextShield v2.2

**Q: Does TextShield fetch URLs?**
A: Never — static regex/indicator analysis only; safe.

**Q: Can I run without internet?**
A: Yes — ML + rules + hashing fallback work offline; RAG/LLM/providers degrade gracefully.

**Q: Which LLM?**
A: `ollama` local (`llama3.1:8b`), `openai` compatible, `nvidia`, or `none` (template).

**Q: How to add dataset?**
A: Drop CSV to `data/raw/`, run `scripts/prepare_dataset.py` + `train_model.py`.

**Q: How to add threat provider?**
A: Copy `openphish/` template (6 files) + `GET /api/v2/threat/providers/{name}`.

**Q: Production DB?**
A: SQLite WAL fine single-instance; for HA use Postgres (roadmap v2.3).

**Q: Coverage 64% not 95%?**
A: Legacy flats at 0% drag; new code ~88%; see `docs/production/Known_Issues.md`.

**Q: License?**
A: MIT (`pyproject.toml`), citation BibTeX in README.

See `docs/Developer_Guide.md`.
