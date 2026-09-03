# PhishTank Provider

## Overview
PhishTank provider lives at `app/threat/providers/phishtank/`. Mirrors Google Safe Browsing / VirusTotal architecture; plugs into `IThreatProvider` with zero engine changes. Uses the PhishTank `checkurl` API.

## Capabilities
- URL reputation
- Phishing metadata (in_database, verified, valid, phish_id, phish_detail_url, submission/verification times)
- Verification status
- Phishing details

**Supported lookups:** `URL` reputation + metadata. Domain / IP / Hash return `None` gracefully.

## Architecture
```
phishtank/
  config.py    # PhishTankConfig — ttl 1800, timeout 5, max_retries 3, backoff 2, rate_limit 30, api_url
  models.py    # PhishTankRequest / PhishTankResponse (in_database, verified, valid, phish_id, detail_url)
  validator.py # URL validation + sanitize
  client.py    # PhishTankClient — async, retry, rate-limit, cache
  mapper.py    # response_to_indicator (phishing vs benign), indicator_to_evidence
  provider.py  # PhishTankProvider — lifecycle + async lookups, health, metadata
```

## Interface
Same `IThreatProvider` surface as GSB/VT. Extra: `PhishTankResponse.is_phishing = in_database and valid`. Confidence 0.95 if verified else 0.78.

- Async `lookup_url`
- Cache (TTL 1800, in-memory keyed by sanitized URL)
- Retry (exponential backoff with jitter)
- Rate limiting (default 30/min, stricter due to PhishTank quota)
- `metadata` exposes name/version/enabled/capabilities/ttl/timeout/api_key_configured/api_url/rate_limit_per_minute/max_retries
- Normalized `ThreatIndicator` output; `PhishTankResponse` never leaks (mapper boundary)
- `health_check` + graceful degrade (`None` on disabled/invalid/error)

## Normalization
`in_database && valid` → `ThreatIndicator(detection_status="phishing")`
- verified+valid → severity critical/high, confidence 0.95, explanation includes phish_id
- unverified valid → high, 0.78
- !is_phishing → `None` (benign) → no indicator (so `response_to_evidence` returns `None`)

Example explanation: `PhishTank: Verified phishing URL (id 1234567, confidence 0.95)`

## Configuration
| key | default |
|-----|---------|
| api_key | "" |
| enabled | true |
| ttl | 1800 |
| timeout | 5.0 |
| max_retries | 3 |
| backoff_factor | 2.0 |
| rate_limit_per_minute | 30 |
| api_url | https://checkurl.phishtank.com/checkurl/ |

## API
```
GET /v2/threat/providers/phishtank
GET /api/v2/threat/providers/phishtank
```

## Failure Behaviour
- Invalid URL → `ValueError` in client, provider catches → `None`.
- Transient network errors retried up to `max_retries`; persistent failure increments `_error_count` and degrades.
- Rate limit blocks via `_wait_for_rate_limit`.

## Testing
`tests/threat/providers/test_phishtank.py` covers config/models/validator/mapper (verified vs unverified vs benign), client cache/rate-limit/retry/invalid, provider lifecycle/disabled/request-object/graceful degrade. Integration via `test_integration.py`.

## Limitations
- Offline heuristic simulation; production must POST to PhishTank with `url` + `format=json` + API key via `aiohttp`.
- No IP/domain/hash intelligence.

## Integration
Used by `routes_threat_providers.py:_get_provider("phishtank")` and `ThreatCoordinator` same path as GSB/VT.
