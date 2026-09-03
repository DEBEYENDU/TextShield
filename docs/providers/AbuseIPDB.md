# AbuseIPDB Provider

## Overview
AbuseIPDB (`app/threat/providers/abuseipdb/`) provides IP reputation via Abuse Confidence Score (0–100). Same architecture as GSB/VT: `IThreatProvider`, async, cache, retry, rate-limit, normalized evidence, health, degrade. Unique among the four: handles **IPv4 and IPv6**.

## Capabilities
- IP reputation
- Abuse confidence (0–100 → mapped to confidence/severity)
- IPv4
- IPv6
- Blacklist status / whitelisted handling

**Supported lookups:** `IP` (IPv4 + IPv6). URL/Domain/Hash return `None`.

## Architecture
```
abuseipdb/
  config.py    # AbuseIPDBConfig — ttl 900, timeout 5, max_retries 3, backoff 2, rate_limit 20, api_url, abuse_threshold 25
  models.py    # AbuseIPDBRequest (ip_address, max_age_days) / AbuseIPDBResponse (abuseConfidenceScore, isWhitelisted, totalReports, numDistinctUsers, lastReportedAt, countryCode, domain)
  validator.py # is_valid_ipv4 / ipv6 / ip, validate_lookup_input, sanitize_ip, detect_ip_version
  client.py    # AbuseIPDBClient — async, retry, rate-limit, cache (TTL 900), whitelisted cache
  mapper.py    # response_to_indicator (whitelisted→benign, score≥threshold→malicious), indicator_to_evidence
  provider.py  # AbuseIPDBProvider — lookup_ip + graceful degradations for other types
```

## Interface
- `lookup_ip(ip: str) -> ThreatIndicator | None`
- `lookup_url/domain/hash` → `None`
- Supports `LookupRequest` object as arg (engine compatibility): `if hasattr(ip, "ioc"): ip = ip.ioc`
- `metadata` → name `abuseipdb`, version `1.0.0`, capabilities `["ip_reputation","abuse_confidence","ipv4","ipv6","blacklist_status"]`, ttl, timeout, api_key_configured, api_url, rate_limit_per_minute, max_retries, abuse_threshold
- `health_check` same shape as other providers
- `AbuseIPDBResponse` never leaves provider layer.

## Normalization
`AbuseIPDBResponse.abuse_confidence_score` → `ThreatIndicator`:
- whitelisted → `is_malicious=False` → `None` (benign) regardless of score
- score < threshold (default 25) → `None` (benign/low)
- score ≥ threshold → `ThreatIndicator(detection_status="malicious"/"suspicious", confidence=score/100, severity)`

Severity mapping:
- 0–24 → low (but filtered as benign → None)
- 25–49 → medium
- 50–74 → high
- 75–100 → critical

IOC type: `':' in ip` → `ipv6` else `ipv4` (maps to `IOCType.IPV6/IPV4`). Explanation: `AbuseIPDB: IP 203.0.113.1 has abuse confidence 92% (42 reports from 15 users)`

## Configuration
| key | default |
|-----|---------|
| api_key | "" |
| enabled | true |
| ttl | 900 |
| timeout | 5.0 |
| max_retries | 3 |
| backoff_factor | 2.0 |
| rate_limit_per_minute | 20 (conservative due to AbuseIPDB quota: 1000/day free) |
| api_url | https://api.abuseipdb.com/api/v2/check |
| abuse_threshold | 25 (minimum score to flag malicious) |

## API
```
GET /v2/threat/providers/abuseipdb
GET /api/v2/threat/providers/abuseipdb
```
Response includes `metadata.rate_limit_per_minute`, `abuse_threshold`, health.

## Failure & Rate Limit
- Invalid IP → ValueError → provider `None`.
- Whitelisted IPs (8.8.8.8, 1.1.1.1, 127.0.0.1, ::1) → benign 0 score.
- Transient errors retried; persistent → degraded `None` + `_error_count`.
- Rate limit 20/min; `_wait_for_rate_limit` polls.
- Heuristic offline: `203.0.113.1`, `198.51.100.1`, `192.0.2.1`, `2001:db8::*` flagged; 8.8.8.8 etc whitelisted. Production should GET `api_url?ipAddress=...&maxAgeInDays=30` with `Key: api_key`.

## Testing
`tests/threat/providers/test_abuseipdb.py` covers validator (v4/v6), config, models (is_malicious, whitelisted), mapper (critical/high/medium/benign, ipv6), client cache/rate-limit/retry/invalid/ipv6, provider lifecycle, ipv6, disabled, graceful degrade. Integration covers API and async suite.

## Limitations
- Heuristic simulation without live API key; real deployment needs valid AbuseIPDB key.
- No URL/domain/hash intelligence.

## Integration
Via `routes_threat_providers.py:_get_provider("abuseipdb")` and `ThreatCoordinator`. Aggregation treats IP evidence alongside URL evidence; `abuse_confidence` usable for scoring.

## IPv6 Support Notes
IPv6 detection via `ipaddress.IPv6Address`; cache and mapping handle `:` detection; tested with `2001:db8::1`.
