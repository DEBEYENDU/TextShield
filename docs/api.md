# TextShield — REST API Reference

Base URL: `http://127.0.0.1:8000` (configurable via `APP_HOST` / `APP_PORT`).
Interactive docs: `GET /docs` (Swagger UI).

## Conventions

- Request/response bodies are JSON.
- Validation failures return **422**; missing model **503**; auth not used.
- All endpoints are validated through Pydantic schemas in
  `app/schemas/analysis.py`.

---

## POST /api/analyze

Analyze a message. `input_type` is `sms` | `text` | `email`.

### SMS / TEXT body

```json
{
  "input_type": "sms",
  "message": "Congratulations! You have won a cash prize. Click now."
}
```

### EMAIL body (structured)

```json
{
  "input_type": "email",
  "subject": "Your account requires verification",
  "sender": "support@secure-update-bank.xyz",
  "body": "Dear customer, verify within 24 hours to avoid blocking."
}
```

### EMAIL body (raw pasted email)

```json
{
  "input_type": "email",
  "email_raw": "From: x@y.zz\nSubject: Hello\n\nBody here..."
}
```

### Response (200)

```json
{
  "classification": "SPAM",
  "confidence": 0.988,
  "risk_level": "HIGH",
  "message_type": "sms",
  "indicators": [
    {"indicator": "Prize / lottery claim", "severity": "high",
     "category": "prize", "evidence": "you have won"}
  ],
  "urls": [
    {"url": "http://bit.ly/xyz", "scheme": "http", "host": "bit.ly",
     "is_shortened": true, "has_ip_host": false, "suspicious_tld": false,
     "suspicious_chars": false, "path_keywords": [],
     "warnings": ["URL is shortened with a known link shortener"],
     "flag_count": 1}
  ],
  "rag_evidence": [
    {"document": "Lottery and prize scams ...",
     "source": "lottery_prize_scam.md", "category": "sms_scams",
     "chunk_id": "sms_scams:lottery_prize_scam:1", "score": 0.62,
     "is_example": false}
  ],
  "explanation": "This message was classified as SPAM ...",
  "explanation_source": "template",
  "recommended_action": "Do not click any links ...",
  "risk_factors": ["ML classified the message as SPAM (confidence 99%)", "..."],
  "model_used": "Linear SVM",
  "rag_status": {"ready": true, "backend": "chromadb",
                 "embedding_provider": "sentence_transformers",
                 "chunk_count": 105, "document_count": 28,
                 "categories": ["banking_scams", "...", "..."],
                 "built_at": "2026-08-10T12:00:00+00:00"},
  "disclaimer": "This analysis is informational ..."
}
```

### Errors

| Status | Condition |
|---|---|
| 422 | empty/missing content, too-long input, invalid `input_type` |
| 503 | ML model not trained (`python scripts/train_model.py`) |
| 500 | unexpected internal failure (logged) |

---

## GET /api/history

Query parameters:

| Param | Values | Default |
|---|---|---|
| `input_type` | `sms` `text` `email` | none |
| `classification` | `SPAM` `HAM` | none |
| `risk_level` | `LOW` `MEDIUM` `HIGH` | none |
| `limit` | 1–200 | 50 |
| `offset` | ≥0 | 0 |
| `order_by` | `timestamp` `id` `classification` `risk_level` `confidence` `input_type` | `timestamp` |
| `direction` | `asc` `desc` | `desc` |

```json
{
  "items": [
    {"id": 7, "timestamp": "2026-08-10T12:00:00+00:00",
     "input_type": "sms",
     "message_hash": "9f86d081884c7d659a2feaa0c55ad015...",
     "classification": "SPAM", "confidence": 0.988,
     "risk_level": "HIGH", "preview": null}
  ],
  "total": 7, "limit": 50, "offset": 0
}
```

---

## DELETE /api/history/{id}

Deletes one entry. `200 {"deleted": true, "id": 7}` or `404`.

## DELETE /api/history

Clears all history. `200 {"deleted": true, "rows_deleted": 7}`.

---

## GET /api/stats

```json
{
  "total_analyses": 42,
  "spam_count": 17,
  "ham_count": 25,
  "spam_percentage": 40.5,
  "average_confidence": 0.93,
  "risk_distribution": {"LOW": 25, "MEDIUM": 9, "HIGH": 8},
  "message_type_distribution": {"sms": 30, "text": 8, "email": 4},
  "analyses_per_day": [{"date": "2026-08-09", "count": 3}],
  "latest_analysis_at": "2026-08-10T12:00:00+00:00"
}
```

---

## GET /api/model-info

```json
{
  "available": true,
  "algorithm": "Linear SVM",
  "trained_at": "2026-08-10T11:00:00+00:00",
  "dataset": {"train_rows": 211, "test_rows": 53},
  "label_mapping": {"ham": 0, "spam": 1},
  "metrics": {"accuracy": 0.9623, "precision_spam": 0.9375,
              "recall_spam": 0.9375, "f1_spam": 0.9375,
              "f1_weighted": 0.9623, "confusion_matrix": [[36, 1], [1, 15]],
              "training_seconds": 0.03},
  "comparison": {
    "Multinomial Naive Bayes": {"metrics": {...}},
    "Logistic Regression": {"metrics": {...}},
    "Linear SVM": {"metrics": {...}}
  }
}
```

---

## GET /api/health

```json
{
  "status": "ok",
  "version": "1.0.0",
  "model_ready": true,
  "rag_ready": true,
  "vector_db_backend": "chromadb",
  "embedding_provider": "sentence_transformers",
  "llm_provider": "ollama",
  "llm_model": "llama3.1:8b",
  "llm_available": false,
  "history_rows": 7
}
```

`status` is `"degraded"` when the ML model is missing (the analyze endpoint
will then return 503).

---

## GET /api/knowledge-base

```json
{
  "ready": true,
  "backend": "chromadb",
  "embedding_provider": "sentence_transformers",
  "chunk_count": 105,
  "document_count": 28,
  "categories": ["banking_scams", "email_scams", "examples", "..."],
  "built_at": "2026-08-10T12:00:00+00:00"
}
```

## POST /api/knowledge-base/rebuild

Rebuilds the vector database from `knowledge_base/`. Returns the same shape
as the GET endpoint, or `500` with a failure detail.