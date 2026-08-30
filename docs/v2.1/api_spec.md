# TextShield v2.1 API Specification

## Base URL
`http://localhost:8000` (development)
`https://api.textshield.io` (production)

## Authentication

### API Key
Send API key via `X-API-Key` header:
```
X-API-Key: your-api-key-here
```

### JWT Bearer Token
Send JWT via `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### RBAC Roles
Each authenticated user has one of these roles:
- `admin` - Full access
- `analyst` - Can analyze and view history
- `developer` - SDK and webhook management
- `readonly` - View only
- `guest` - Public endpoints only

## Endpoints

### GET /api/v2/system/health
**Description:** Check system health status.

**Responses:**
- `200` - System healthy
  ```json
  {
    "cpu": {"usage_percent": 45.2, "core_count": 8},
    "memory": {"usage_percent": 62.1, "total_bytes": 17179869184},
    "disk": {"usage_percent": 31.5, "total_bytes": 500107862016},
    "services": {
      "database": {"healthy": true},
      "vector_db": {"healthy": true},
      "llm": {"healthy": true},
      "embedding_model": {"healthy": true}
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

### GET /api/v2/system/version
**Description:** Get TextShield version information.

**Responses:**
- `200` - Version info
  ```json
  {
    "version": "2.1.0",
    "name": "TextShield V2.1 - Enterprise Integration Layer",
    "build": "6557046",
    "python_version": "3.14.6"
  }
  ```

### POST /api/v2/analyze
**Description:** Analyze a single message for spam/phishing/fraud.

**Request:**
```json
{
  "text": "Your package is waiting for you at the delivery center. Click here to claim!",
  "include_explanation": true
}
```

**Headers:**
```
X-API-Key: your-api-key-here
Authorization: Bearer <jwt-token>
```

**Responses:**
- `200` - Successful analysis
  ```json
  {
    "classification": "spam",
    "risk_level": "high",
    "confidence": 0.94,
    "intent": {
      "primary_intent": "fraud",
      "confidence": 0.87,
      "secondary_intents": [{"intent": "phishing", "confidence": 0.62}]
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

- `400` - Bad request (empty or invalid text)
- `401` - Authentication required
- `403` - Insufficient permissions

### POST /api/v2/batch
**Description:** Analyze multiple messages asynchronously.

**Request:**
```json
{
  "texts": [
    "Your package is waiting for you at the delivery center. Click here to claim!",
    "Meeting at 3 PM today in the conference room.",
    "Your bank account has been compromised. Update your security settings now."
  ]
}
```

**Responses:**
- `202` - Accepted (async processing)
  ```json
  {
    "job_id": "batch_a1b2c3d4e5f6",
    "status": "pending",
    "total_messages": 3,
    "message": "Batch analysis started - use polling to check status"
  }
  ```

**Polling:**
- `GET /api/v2/history?skip=0&limit=1&classification=batch_a1b2c3d4e5f6`
- Or check specific job status via history queries

### GET /api/v2/history
**Description:** Get analysis history with pagination and filtering.

**Query Parameters:**
- `skip` (int, default 0) - Number of records to skip
- `limit` (int, default 50) - Maximum records to return
- `classification` (string, optional) - Filter by classification (spam/ham/phishing/etc.)

**Responses:**
- `200` - History returned
  ```json
  {
    "items": [
      {
        "id": 1,
        "classification": "spam",
        "risk_level": "high",
        "confidence": 0.94,
        "message_type": "email",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 150,
    "skip": 0,
    "limit": 50
  }
  ```

### GET /api/v2/history/{record_id}
**Description:** Get a specific analysis record by ID.

**Responses:**
- `200` - Record found
  ```json
  {
    "record": {
      "id": 1,
      "text": "Your package is waiting...",
      "classification": "spam",
      "risk_level": "high",
      "confidence": 0.94,
      "intent": {"primary_intent": "fraud"},
      "evidence": [...],
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
  ```

- `404` - Record not found

### DELETE /api/v2/history/{record_id}
**Description:** Delete an analysis record.

**Responses:**
- `200` - Record deleted
  ```json
  {
    "deleted": true,
    "record_id": 1
  }
  ```

- `404` - Record not found

### GET /api/v2/system/metrics
**Description:** Get system performance metrics.

**Responses:**
- `200` - Metrics
  ```json
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "system": {
      "cpu": {"usage_percent": 45.2, "core_count": 8},
      "memory": {"usage_percent": 62.1, "total_bytes": 17179869184}
    },
    "process": {
      "memory_bytes": 536870912,
      "cpu_percent": 12.5,
      "num_threads": 4
    }
  }
  ```

### POST /api/v2/webhooks
**Description:** Register a new webhook subscription.

**Request:**
```json
{
  "url": "https://example.com/webhooks/textshield",
  "events": ["analysis_completed", "batch_completed"],
  "secret": "webhook-secret-for-signing",
  "headers": {
    "X-Custom-Header": "value"
  }
}
```

**Responses:**
- `201` - Webhook created
- `400` - Invalid URL or events
- `401` - Authentication required

### GET /api/v2/plugins
**Description:** List loaded plugins.

**Responses:**
- `200` - Plugins list
  ```json
  {
    "plugins": [
      {
        "name": "spam_patterns",
        "version": "1.0.0",
        "capabilities": ["classification", "risk_scoring"]
      }
    ],
    "total": 1
  }
  ```

## Error Responses

### Standard Error Format
```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "code": "ERR_TYPE",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v2/analyze"
}
```

### Common Error Codes
- `400` - Bad Request - Invalid input
- `401` - Unauthorized - Missing or invalid authentication
- `403` - Forbidden - Insufficient permissions
- `404` - Not Found - Endpoint or resource not found
- `429` - Too Many Requests - Rate limit exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable - System temporarily unavailable

### Specific Error Examples
- **Missing API key:**
  ```json
  {
    "error": "authentication_required",
    "message": "Authentication header required",
    "code": "ERR_AUTH_001",
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

- **Invalid API key:**
  ```json
  {
    "error": "invalid_api_key",
    "message": "The provided API key is invalid or expired",
    "code": "ERR_AUTH_002",
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

- **Insufficient permissions:**
  ```json
  {
    "error": "insufficient_permissions",
    "message": "Admin role required for this operation",
    "code": "ERR_AUTH_003",
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

- **Validation error:**
  ```json
  {
    "error": "validation_error",
    "message": "Text field is required and must not be empty",
    "code": "ERR_VALID_001",
    "timestamp": "2024-01-15T10:30:00Z",
    "details": {"text": ["Text field is required"]}
  }
  ```

## Rate Limits
- Default: 100 requests per 60 seconds per API key
- Adjustable via `RateLimitMiddleware`
- Headers included in response:
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: 95
  - `X-RateLimit-Reset`: timestamp when limit resets

## Versioning
- Current version: `v2.1`
- Future: `v3.0` will include breaking changes
- Deprecated endpoints will have 6-month deprecation notice