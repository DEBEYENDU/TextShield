# TextShield v2.1 Authentication Guide

## Overview
TextShield v2.1 supports two primary authentication methods: API Keys and JWT (JSON Web Tokens). Both can be used interchangeably, and the system supports Role-Based Access Control (RBAC) with five defined roles.

## Authentication Methods

### 1. API Key Authentication
Simple and suitable for server-to-server communication or script-based usage.

#### Getting an API Key
API keys are managed through the admin interface or via the API:
```bash
# Example: Register a new API key
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d {
    "name": "my-script",
    "roles": ["analyst"],
    "expires_at": "2025-01-15T00:00:00Z"
  }
```

#### Using an API Key
Include the API key in the `X-API-Key` request header:
```
X-API-Key: abc123def456ghi789
```

#### API Key Best Practices
- Store API keys securely (environment variables, secret managers)
- Rotate keys regularly
- Assign minimal required roles to each key
- Monitor key usage via the analytics endpoint
- Revoke compromised keys immediately

### 2. JWT (JSON Web Token) Authentication
Recommended for browser-based applications or client-server scenarios where tokens should have shorter lifetimes.

#### Obtaining a JWT Token
Authenticate via the login endpoint to receive a token:

```bash
# Example: Login to get JWT
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/json" \
  -d {
    "api_key": "your-api-key",
    "username": "user@example.com"
  }
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "roles": ["analyst"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Using a JWT Token
Include the token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### JWT Token Lifecycle
- **Default expiration:** 30 minutes (configurable via `jwt_expiration_minutes`)
- **Refresh:** Use the refresh endpoint to get a new access token
- **Revocation:** Tokens can be revoked via the admin API
- **Scope:** Tokens carry role information for RBAC

## Role-Based Access Control (RBAC)

### Five Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access: manage users, plugins, settings, all API endpoints |
| **analyst** | Analyze messages, view history, manage own API keys |
| **developer** | SDK usage, manage webhooks, view metrics |
| **readonly** | View analysis results and history only |
| **guest** | Public endpoints only: system health, version |

### Role Hierarchy
```
admin > analyst > developer > readonly > guest
```

A user with a higher role has all permissions of lower roles plus their own.

### Checking Permissions
The API automatically enforces role checks. Example error when insufficient permissions:

```json
{
  "error": "insufficient_permissions",
  "message": "Admin role required for this operation",
  "code": "ERR_AUTH_003",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Middleware Integration

### FastAPI Authentication Middleware
TextShield includes automatic authentication middleware. When enabled, all protected endpoints require authentication.

#### Enabling Middleware
```python
from fastapi import FastAPI
from app.middleware.auth import AuthenticationMiddleware

app = FastAPI()
app.add_middleware(AuthenticationMiddleware)
```

#### Middleware Behavior
- Extracts API key from `X-API-Key` or JWT from `Authorization: Bearer <token>`
- Validates the credential and attaches user roles to `request.state.user`
- Skips public endpoints (health, version, auth login/register)
- Returns `401` if no valid authentication provided
- Returns `403` if valid auth but insufficient role

### Custom Authentication
You can integrate with external authentication providers by modifying the `get_api_key` dependency in `app/authentication/manager.py`.

## SDK Authentication

### Python SDK
```python
from textshield import TextShieldClient

# API Key authentication
client = TextShieldClient(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)

# JWT authentication (omit api_key, use token in requests)
client = TextShieldClient(base_url="http://localhost:8000")
# Token will be sent via Authorization header in individual requests
```

### JavaScript SDK
```javascript
const { TextShieldClient } = require('textshield');

// API Key authentication
const client = new TextShieldClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'your-api-key-here'
});

// JWT authentication (set token per-request or via defaultHeaders)
client.defaultHeaders['Authorization'] = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
```

### Java SDK
```java
TextShieldClient client = new TextShieldClient("http://localhost:8000", "your-api-key-here");

// Or with JWT
TextShieldClient client = new TextShieldClient("http://localhost:8000");
// Set token per request:
client.sendRequest("/analyze", "POST", body);
```

## Security Recommendations

### 1. Transport Security
- **Always use HTTPS in production**
- Never send credentials over plain HTTP
- Configure your load balancer/ reverse proxy to terminate TLS

### 2. API Key Management
```bash
# Recommended: Use environment variables
export TEXT_SHIELD_API_KEY="your-key-here"

# Or: Use a secrets manager
# HashiCorp Vault, AWS Secrets Manager, etc.
```

### 3. Token Security
- Store JWT tokens securely (httpOnly cookies, secure storage)
- Implement token refresh logic in clients
- Set appropriate token expiration times
- Implement token revocation for compromised tokens

### 4. Network Security
- Restrict API access to trusted IP ranges via firewall
- Use a reverse proxy (nginx, Traefik) with additional security headers
- Enable CORS only for trusted origins

### 5. Audit Logging
All authentication events are logged:
- Successful authentications
- Failed authentication attempts
- Token revocations
- Role changes
- API key creations and deletions

Log entries can be viewed via the audit endpoint or through the system monitoring dashboard.

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Missing `X-API-Key` or `Authorization` header
- Invalid or expired API key
- Missing or malformed JWT token
- Token expired (check `exp` claim)

**403 Forbidden**
- Valid authentication but insufficient role
- Trying admin-only operation with analyst role
- Plugin operation requires developer role

**Rate Limit Exceeded**
- Too many requests in the current window
- Check `X-RateLimit-*` response headers
- Implement exponential backoff in clients
- Contact admin to increase rate limit if needed

**Certificate Errors (HTTPS)**
- Ensure your SSL certificate is valid
- Add the certificate to your trust store if self-signed
- Use `verify=False` only for testing (not recommended)

## Migration from v1.0

### API Key Compatibility
- v1.0 API keys continue to work in v2.1
- New v2.1 endpoints use the same authentication
- v1.0 endpoints are marked as legacy with deprecation notices

### JWT Introduction
- v1.0 used API keys only
- v2.1 adds JWT as an alternative
- Both methods can be used simultaneously
- No migration required for existing API keys

### RBAC
- v1.0 had no built-in RBAC
- v2.1 introduces 5 roles with automatic enforcement
- Existing users can be assigned roles via the admin API
- Permissions are checked on a per-endpoint basis