# URLhaus Provider

## Overview
URLhaus (`app/threat/providers/urlhaus/`) integrates Abuse.ch URLhaus API for malware URL intelligence. Same architecture as GSB/VT: `IThreatProvider`, async, cache, retry, rate-limit, normalized evidence, health, degrade.

## Capabilities
- Malware URL detection
- Malware payload metadata (threat type, tags, payload signatures, blacklists, url_status, date_added)
- Threat type classification (malware_download / trojan / ransomware / etc.)

**Supported lookups:** `URL` only (malware URLs). Domain/IP/Hash return `None`.

## Architecture
```
urlhaus/
  config.py    # URLhausConfig — ttl 600, timeout 5, max_retries 3, backoff 2, rate_limit 40, api_url
  models.py    # URLhausRequest / URLhausResponse (query_status, threat, blacklists, payloads, tags, url_status)
  validator.py # URL validation
  client.py    # URLhausClient — async, retry, rate-limit, cache (TTL 600)
  mapper.py    # response_to_indicator (ok+threat → malware), indicator_to_evidence
  provider.py  # URLhausProvider
```

## Interface
- `lookup_url(url: str) -> ThreatIndicator | None`
- `lookup_domain/ip/hash` → `None` (not supported, graceful)
- `metadata` includes name `urlhaus`, version `1.0.0`, capabilities, ttl, timeout, api_key_configured, api_url, rate_limit_per_minute, max_retries
- `capabilities()` → `["malware_url_detection", "malware_payload_metadata", "threat_type_classification"]`
- `health_check()` → `{healthy, last_check, error, initialized, request_count, error_count, enabled}`
- Raw `URLhausResponse` never escapes provider layer.

## Normalization
`query_status == "ok" and threat != None` → malicious. Severity mapped from `threat`:
- ransomware/trojan/stealer → critical
- malware_download/malware → high
- other → medium
Confidence 0.91 (heuristic). Explanation includes threat and payload signatures: `URLhaus: Malware URL detected (threat=trojan, confidence 0.91) payloads: Trojan.Generic`

Cache keyed by sanitized URL, TTL 600 (short due to fast-changing malware feeds).

## Configuration
| key | default |
|-----|---------|
| api_key | "" |
| enabled | true |
| ttl | 600 |
| timeout | 5.0 |
| max_retries | 3 |
| backoff_factor | 2.0 |
| rate_limit_per_minute | 40 |
| api_url | https://urlhaus-api.abuse.ch/v1/url/ |

## API
```
GET /v2/threat/providers/urlhaus
GET /api/v2/threat/providers/urlhaus
```
Returns `{provider, metadata, health, capabilities}`.

## Failure & Rate Limit
- Invalid URL → ValueError → provider `None`.
- Transient errors retried with backoff + jitter; persistent → degraded `None`.
- Rate limit sliding window 60s; `_wait_for_rate_limit` polls 0.2s.
- Heuristic offline: URLs containing `malware`, `payload`, `exe`, `trojan`, `ransomware` or explicit `urlhaus-malicious` are flagged.

## Testing
`tests/threat/providers/test_urlhaus.py` covers config, models (`is_malicious`), validator, mapper (critical vs high vs benign), client cache/rate-limit/retry/invalid, provider lifecycle/disabled/graceful degrade. `test_integration.py` verifies API.

## Limitations
- No live Abuse.ch call in heuristic mode; production should POST `{"url": url}` to URLhaus API via `aiohttp`.
- No IP/domain/hash.

## Integration
Via `routes_threat_providers.py` and `ThreatCoordinator` same as GSB/VT; aggregation can treat `detection_status="malware"` alongside phishing.
