# Privacy Model — Threat Intelligence

## Principles

- Do NOT turn TextShield into a URL crawler
- Do NOT automatically visit arbitrary URLs
- Do NOT expose user messages unnecessarily to external services
- Threat intelligence providers are optional and configurable

## Data Minimization

Before sending an IOC externally:
- Determine whether the IOC can be safely shared
- Never send entire original message when only IOC is required
- Prefer: URL, domain, hash, IP
- Avoid: full message, email body, personal conversation

## Controls

PrivacyPolicy:
- `allow_external` flag disables all external lookups
- `shareable_value(ioc)` returns normalized IOC; for emails returns `email-hash:<hash>` to external providers
- Unsupported IOC types raise `PrivacyViolationError` and block sharing

## Secrets

API keys must never be hardcoded, committed, logged, returned by APIs, or included in errors.

Use environment configuration:
TEXTSHIELD_GOOGLE_SAFE_BROWSING_KEY
TEXTSHIELD_VIRUSTOTAL_API_KEY

Never expose secrets in frontend JavaScript.

## Logging

Do NOT log API keys. Avoid logging complete message content. Log provider, IOC type, request duration, cache hit/miss, provider status, rate-limit events.

## Offline Mode

TextShield remains fully usable without external APIs. Local intelligence, static analysis, knowledge graph, RAG, ML, LLM provide full analysis.

## User Consent

External lookups can be disabled via config `allow_external_lookups`. UI shows provider status.

## Data Retention

Cache stores IOC, provider, result, timestamp, expiration. TTL configurable. Reputation store persists local sightings. No raw messages stored in threat-intel DB.
