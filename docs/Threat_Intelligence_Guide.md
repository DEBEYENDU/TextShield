# Threat Intelligence Guide — TextShield v2.2

## Platform
Provider-independent layer between providers and decision engine (never modifies core ML).

## Flow
`IOCEngine → CacheManager → ThreatCoordinator → Providers(6) → Aggregation → EvidenceEngine → Decision → Dashboard`

## IOC
`app/threat/ioc/` 7 extractors (URL/Domain/IPv4/IPv6/Email/Phone/ShortURL), `normalizer` (scheme lower, punctuation strip), `validator`. `POST /api/v2/ioc/extract`.

## Cache
`CacheRecord` (provider, threat_status, score, TTL, revision), `InMemoryStorage` + JSON `PersistentStorage`, `manager CRUD + bulk`, `Lru/TtlEviction`, `Cleanup`, `serializer`, `statistics` (hit_ratio). `GET /api/v2/threat/cache`.

## Lookup Engine
`coordinator/scheduler/dispatcher/executor` (sem 10) + `RetryPolicy` (exp backoff jitter) + `TimeoutManager` + `CircuitBreaker` (CLOSED/OPEN/HALF-OPEN) + `metrics`. Isolated per provider.

## Providers
`google_safe_browsing`, `virustotal` (GSB 0.35, VT 0.30 weight), `openphish` 0.15, `phishtank` 0.10, `urlhaus` 0.10, `abuseipdb` IP. Each `provider/client/mapper/models/validator/config`, cache-first, normalized `ThreatEvidence`.

## Aggregation
`aggregation/{weighting,confidence,funnel,fusion}` → `ThreatProfile` (overall_threat_score, confidence 5-factor, severity informational→critical, provider_agreement, reliability_score, reasoning_summary).

## Evidence
Unified engine `app/evidence/` + `app/threat/aggregation` graphs chain `message → IOC → cache → providers → aggregation → evidence → decision`.

See `docs/IOC_Extraction.md`, `Threat_Cache.md`, `Threat_Execution.md`, `Threat_Aggregation.md`, `Unified_Evidence.md`, `docs/providers/*`.
