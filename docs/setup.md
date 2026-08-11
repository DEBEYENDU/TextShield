# TextShield — Setup Guide

## 1. Requirements

- Python **3.10 – 3.14**
- ~2 GB free disk (with optional PyTorch-based embeddings)
- Internet connection on first run (package install + optional model download)

## 2. Install

```bash
cd TextShield
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Notes:

- `sentence-transformers` pulls in PyTorch (CPU version by default on most
  platforms). If you want to skip it: remove the line from
  `requirements.txt` — the app falls back to the hashing embedder.
- `chromadb` is likewise optional; a dependency-free numpy store takes over.
- On a freshly created `.env`, defaults are fine for a first run.

## 3. Quick start (3 commands)

```bash
python scripts/prepare_dataset.py       # 1. dataset from data/raw/
python scripts/train_model.py           # 2. train + save best model
python scripts/build_knowledge_base.py  # 3. index the RAG knowledge base
python run.py                           # 4. open http://127.0.0.1:8000
```

## 4. Configuration (`.env`)

Copy `.env.example` → `.env`. Relevant variables:

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` / `APP_HOST` / `APP_PORT` | development / 127.0.0.1 / 8000 | server |
| `DATABASE_URL` | `sqlite:///./textshield.db` | history DB |
| `HISTORY_STORE_PREVIEW` | `false` | store truncated message preview |
| `MAX_MESSAGE_LENGTH` | 10000 | input length limit |
| `MODEL_PATH` / `VECTORIZER_PATH` / `MODEL_METADATA_PATH` / `MODEL_METRICS_PATH` | `models/...` | artifacts |
| `VECTOR_DB_PATH` | `vector_db` | vector store location |
| `RAG_TOP_K` | 4 | retrieval depth |
| `EMBEDDING_PROVIDER` | `sentence_transformers` | `sentence_transformers` \| `hashing` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | transformer model name |
| `LLM_PROVIDER` | `ollama` | `ollama` \| `openai` \| `nvidia` \| `none` |
| `LLM_MODEL` | *(empty)* | model name for the chosen provider |
| `LLM_BASE_URL` | `http://localhost:11434` | provider endpoint |
| `LLM_API_KEY` | *(empty)* | only for openai/nvidia |
| `LLM_TIMEOUT_SECONDS` | 30 | generation timeout |

### LLM examples

Ollama (local):

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
```

OpenAI-compatible:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
```

NVIDIA NIM:

```env
LLM_PROVIDER=nvidia
LLM_MODEL=meta/llama-3.3-70b-instruct
LLM_API_KEY=nvapi-...
```

## 5. Datasets

`data/README.md` documents the expected structure (generic `text,label`
CSVs) and the recommended UCI SMS Spam Collection. Place additional CSVs in
`data/raw/`, re-run `scripts/prepare_dataset.py`, then retrain.

## 6. Testing

```bash
python -m pytest          # 73 tests
```

The test suite auto-trains the model on a fresh checkout (session fixture),
so `pytest` works without running the training step manually.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: sklearn` | activate the venv (`pip install -r requirements.txt` inside it) |
| `POST /api/analyze` → 503 | run `python scripts/train_model.py` |
| RAG evidence empty | run `python scripts/build_knowledge_base.py` |
| `sentence-transformers` install fails | remove it from requirements; hashing fallback activates |
| ChromaDB import errors | remove chromadb from requirements; numpy fallback activates |
| First analyze is slow | the embedding model downloads once (~90 MB) |
| Port already in use | `APP_PORT=8001` in `.env` |
| GPU errors on embedded devices | use `EMBEDDING_PROVIDER=hashing` |
| Changes not applied | restart uvicorn; `--reload` picks up code but not `.env` changes (restart needed) |

## 8. Production-ish considerations (future)

- Run with `APP_ENV=production` (disables auto-reload).
- Put the app behind a reverse proxy (nginx/Caddy) for TLS.
- Add authentication before exposing beyond localhost.
- Monitor `logs/textshield.log` (rotating, 2 MB × 3).