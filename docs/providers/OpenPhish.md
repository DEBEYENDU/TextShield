# OpenPhish Provider

## Overview
OpenPhish is an open phishing feed provider integrated via `app/threat/providers/openphish/`. It follows the same architecture as Google Safe Browsing and VirusTotal and plugs into `IThreatProvider` without changes to the Threat Execution Engine.

## Capabilities
- URL reputation (phishing detection)
- Feed intelligence (openphish.com/feed.txt)

**Supported lookups:** `URL` only. Domain / IP / Hash gracefully return `None`.

## Architecture
```
openphish/
  config.py    # OpenPhishConfig — ttl, timeout, max_retries, backoff_factor, rate_limit_per_minute, feed_url
  models.py    # OpenPhishRequest / OpenPhishResponse (raw) + ThreatEvidence (normalized)
  validator.py # is_valid_url, validate_lookup_input, sanitize_url
  client.py    # OpenPhishClient — async HTTP, retry, rate-limit, cache
  mapper.py    # response_to_indicator / indicator_to_evidence / response_to_evidence
  provider.py  # OpenPhishProvider — IThreatProvider, lifecycle, health, lookups
  __init__.py  # public exports
```

## Interface
Implements: `name`, `version`, `enabled`, `metadata`, `capabilities`, `initialize`, `shutdown`, `health_check`, `lookup_url`, `lookup_domain`, `lookup_ip`, `lookup_hash`.

- Async execution via `async def lookup_url`
- Cache integration via in-memory `client._cache` with TTL
- Retry policy via `max_retries` + exponential backoff (`backoff_factor`)
- Rate limiting via sliding 60s window (`rate_limit_per_minute` default 60)
- Exposes `metadata` (name, version, capabilities, ttl, timeout, api_key_configured, feed_url, rate_limit_per_minute, max_retries)
- Returns `ThreatIndicator` (normalized); raw `OpenPhishResponse` never leaves provider layer (enforced in `mapper.py` + `provider.py`)
- `health_check()` returns `{healthy, last_check, error, initialized, request_count, error_count, enabled}`
- Gracefully degrades: invalid input / disabled provider / client exception → `None` (no raise)

## Normalization
`OpenPhishResponse(is_phishing, confidence)` → `ThreatIndicator(detection_status="phishing", confidence, severity)` → `ThreatEvidence` via `indicator_to_evidence`. Confidence ≥0.85 → high, ≥0.6 → medium else low.

## Configuration
| key | default | description |
|-----|---------|-------------|
| api_key | "" | not required (feed is open) |
| enabled | true | toggle provider |
| ttl | 3600 | cache TTL seconds |
| timeout | 5.0 | request timeout |
| max_retries | 3 | retry count |
| backoff_factor | 2.0 | exponential base |
| rate_limit_per_minute | 60 | requests per 60s |
| feed_url | https://openphish.com/feed.txt | feed source |

## API
```
GET /v2/threat/providers/openphish
GET /api/v2/threat/providers/openphish
```
Response: `{provider, metadata, health, capabilities}`

## Failure & Rate-Limit Behaviour
- Transient errors retried with backoff; after max_retries escalates but provider catches and returns `None` (degraded).
- Rate limit exceeded → `_wait_for_rate_limit()` sleeps 0.2s polling until window clears.
- Cache hit bypasses network and rate limit.

## Testing
See `tests/threat/providers/test_openphish.py`: config, models, validator, mapper, client cache/rate-limit/retry, provider lifecycle, disabled, invalid, graceful degrade.

## Limitations
- Heuristic simulation offline (no live feed fetch in tests); production should replace `_do_lookup` with real `aiohttp` feed fetch and URL set membership check.
- No domain/IP/hash intelligence; returns `None`.

## Integration
Registered via `_get_provider("openphish")` in `routes_threat_providers.py`; works with `ThreatCoordinator` + `CacheManager` + `RateLimitManager` without engine changes.
