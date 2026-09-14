# Threat Intelligence v4.0 — RFC-008

Provider-independent Threat Intelligence & IOC Intelligence Platform.

## Architecture

Message → IOC Extraction → IOC Normalization → Local Intelligence (Cache, Previous Findings, Internal Knowledge Base) → Threat Intelligence Providers → Provider Result Normalization → Threat Intelligence Aggregator → Trust / Threat Engine → LLM / Multi-Agent Reasoning → Final Evidence Report

Never crawls URLs. Never visits arbitrary URLs. No automatic external fetching beyond provider lookups.

## IOC Types

url, domain, ipv4, ipv6, email, md5, sha1, sha256

## Providers

Provider abstraction `ThreatIntelProvider` with `lookup_url/domain/ip/hash/email`. Verdicts: known_malicious, suspicious, unknown, benign, unavailable, unsupported.

Registry: dynamic registration, no provider-specific logic scattered.

Current providers:
- mock (offline deterministic)
- static (static URL analysis, domain age, punycode, typosquatting, subdomain depth, shorteners, credential paths, etc.)
- google_safe_browsing (optional, key `TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY`)
- virustotal (optional, key `TEXTSHIELD_VIRUSTOTAL_API_KEY`)

Adapters return `unavailable` when credentials absent. Never crash pipeline.

## Privacy

PrivacyPolicy gates external sharing. Only IOC values are shared, never full message. Email addresses are hashed before external share. External lookups disabled if `allow_external_lookups=False`.

Never log secrets.

## Caching

`ThreatIntelCache` stores IOC × provider × result with TTL. Hit/miss stats exposed via API.

## Rate Limiting

Provider-aware rate limiting per minute/day + concurrency. On limit: queue/skip/use cache.

## Aggregation

Preserves each provider result. Known malicious anywhere → HIGH threat level. Confidence considers provider reliability, agreement, freshness, IOC type, evidence quantity.

Unknown never treated as safe.

## Knowledge Graph Integration

Nodes: Domain, IP, URL, Threat Campaign. Edges: associated_with, hosts, belongs_to, observed_in. Sync after each check.

## RAG Integration

Validated findings become retrievable evidence with source metadata. Only known_malicious/benign from successful lookups inserted.

## LLM / Multi-Agent Integration

Normalized evidence rendered as prompt block. LLM must explain disagreement, never invent results.

Agents receive brief distinguishing known malicious / suspicious / unknown / benign. Unknown stays neutral.

## API

GET /api/threat-intel/providers
GET /api/threat-intel/status
POST /api/threat-intel/check
GET /api/threat-intel/ioc/{ioc}

Response shape includes ioc, results[], aggregated_verdict, confidence, cached.

## Offline Mode

Fully usable without external APIs: static analysis, local IOC DB, knowledge graph, RAG, ML, LLM, behavior analysis.

## Security

No API keys hardcoded/committed/logged/returned. Environment config only.

Malformed inputs, punycode, encoded URLs, extremely long URLs handled safely.

## Configuration

TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY
TEXTSHIELD_VIRUSTOTAL_API_KEY
Cache TTL, rate limits, max IOCs per message via `ThreatIntelConfig`.

## Adding Providers

Implement `ThreatIntelProvider`, register via `ThreatIntelRegistry`. No changes to core.
